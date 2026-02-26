import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  MarkerType,
  addEdge,
  type Connection,
  type Edge,
  type Node,
  useEdgesState,
  useNodesState,
} from "reactflow";
import { toPng } from "html-to-image";
import "reactflow/dist/style.css";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorAlert } from "../components/ui/ErrorAlert";
import { Skeleton } from "../components/ui/Skeleton";
import { extractApiError } from "../utils/errors";
import { toTitleCase } from "../utils/format";
import { listCases } from "./casesApi";
import { createBoardConnection, createBoardItem, deleteBoardConnection, deleteBoardItem, fetchBoard, patchBoardItem } from "./boardApi";
import { listCaseEvidence } from "./evidenceApi";

export function DetectiveBoardPage() {
  const queryClient = useQueryClient();
  const boardRef = useRef<HTMLDivElement | null>(null);
  const [selectedCaseId, setSelectedCaseId] = useState<number>(0);
  const [newNoteTitle, setNewNoteTitle] = useState("");
  const [newNoteText, setNewNoteText] = useState("");
  const [newEvidenceId, setNewEvidenceId] = useState<number>(0);
  const [message, setMessage] = useState("");
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const casesQuery = useQuery({
    queryKey: ["cases"],
    queryFn: listCases,
  });

  const boardQuery = useQuery({
    queryKey: ["detective-board", selectedCaseId],
    queryFn: () => fetchBoard(selectedCaseId),
    enabled: selectedCaseId > 0,
  });

  const evidenceQuery = useQuery({
    queryKey: ["case-evidence", selectedCaseId, "all"],
    queryFn: () => listCaseEvidence(selectedCaseId),
    enabled: selectedCaseId > 0,
  });

  useEffect(() => {
    if (!boardQuery.data) {
      setNodes([]);
      setEdges([]);
      return;
    }

    const mappedNodes: Node[] = boardQuery.data.items.map((item) => ({
      id: String(item.id),
      type: "default",
      position: { x: item.x, y: item.y },
      data: {
        label: (
          <div className="board-node">
            <strong>{item.title || toTitleCase(item.item_type)}</strong>
            <p>{item.text || (item.evidence ? `Evidence #${item.evidence}` : "No details")}</p>
          </div>
        ),
      },
      style: {
        border: "1px solid #8d7c5c",
        borderRadius: 12,
        width: 220,
        background: "#fffef9",
      },
    }));

    const mappedEdges: Edge[] = boardQuery.data.connections.map((connection) => ({
      id: String(connection.id),
      source: String(connection.from_item),
      target: String(connection.to_item),
      style: { stroke: "#b10000", strokeWidth: 2.2 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: "#b10000",
      },
    }));

    setNodes(mappedNodes);
    setEdges(mappedEdges);
  }, [boardQuery.data, setEdges, setNodes]);

  const createItemMutation = useMutation({
    mutationFn: createBoardItem,
    onSuccess: () => {
      setMessage("Board item created.");
      setNewNoteTitle("");
      setNewNoteText("");
      setNewEvidenceId(0);
      queryClient.invalidateQueries({ queryKey: ["detective-board", selectedCaseId] });
    },
    onError: (error) => setMessage(extractApiError(error)),
  });

  const patchItemMutation = useMutation({
    mutationFn: ({ itemId, payload }: { itemId: number; payload: Record<string, unknown> }) => patchBoardItem(itemId, payload),
    onError: (error) => setMessage(extractApiError(error)),
  });

  const deleteItemMutation = useMutation({
    mutationFn: deleteBoardItem,
    onSuccess: () => {
      setMessage("Board item removed.");
      queryClient.invalidateQueries({ queryKey: ["detective-board", selectedCaseId] });
    },
    onError: (error) => setMessage(extractApiError(error)),
  });

  const createConnectionMutation = useMutation({
    mutationFn: createBoardConnection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["detective-board", selectedCaseId] });
    },
    onError: (error) => setMessage(extractApiError(error)),
  });

  const deleteConnectionMutation = useMutation({
    mutationFn: deleteBoardConnection,
    onSuccess: () => {
      setMessage("Connection removed.");
      queryClient.invalidateQueries({ queryKey: ["detective-board", selectedCaseId] });
    },
    onError: (error) => setMessage(extractApiError(error)),
  });

  const boardConnections = useMemo(() => boardQuery.data?.connections || [], [boardQuery.data?.connections]);
  const boardItems = useMemo(() => boardQuery.data?.items || [], [boardQuery.data?.items]);

  async function handleExportBoard() {
    if (!boardRef.current) {
      return;
    }
    try {
      const dataUrl = await toPng(boardRef.current, { cacheBust: true, pixelRatio: 2 });
      const link = document.createElement("a");
      link.download = `detective-board-case-${selectedCaseId}.png`;
      link.href = dataUrl;
      link.click();
      setMessage("Board exported as image.");
    } catch {
      setMessage("Failed to export board image.");
    }
  }

  function onConnect(connection: Connection) {
    if (!connection.source || !connection.target) {
      return;
    }
    setEdges((existing) =>
      addEdge(
        {
          ...connection,
          style: { stroke: "#b10000", strokeWidth: 2.2 },
        },
        existing,
      ),
    );
    createConnectionMutation.mutate({ from_item: Number(connection.source), to_item: Number(connection.target) });
  }

  return (
    <section className="page">
      <h1>Detective Board</h1>
      <p>
        Add notes or evidence references, drag to rearrange reasoning, connect related nodes with red lines, remove links,
        and export the board as an image for reports.
      </p>
      <ErrorAlert message={message} />

      <Card>
        <h2>Board Context</h2>
        <div className="inline-form">
          <select value={selectedCaseId || ""} onChange={(event) => setSelectedCaseId(Number(event.target.value))}>
            <option value="">Select Case</option>
            {casesQuery.data?.map((item) => (
              <option key={item.id} value={item.id}>
                #{item.id} - {item.title}
              </option>
            ))}
          </select>
          <Button onClick={handleExportBoard} disabled={!selectedCaseId}>
            Export Board Image
          </Button>
        </div>
      </Card>

      <div className="cards-grid board-panel-grid">
        <Card>
          <h2>Add Note Item</h2>
          <form
            className="form-grid"
            onSubmit={(event) => {
              event.preventDefault();
              createItemMutation.mutate({
                caseId: selectedCaseId,
                payload: {
                  item_type: "NOTE",
                  title: newNoteTitle,
                  text: newNoteText,
                  x: 60,
                  y: 60,
                },
              });
            }}
          >
            <label>
              Title
              <input value={newNoteTitle} onChange={(event) => setNewNoteTitle(event.target.value)} required />
            </label>
            <label>
              Note
              <textarea value={newNoteText} onChange={(event) => setNewNoteText(event.target.value)} />
            </label>
            <Button type="submit" disabled={!selectedCaseId || createItemMutation.isPending}>
              Add Note
            </Button>
          </form>

          <div className="divider" />
          <h2>Add Evidence Reference</h2>
          <div className="inline-form">
            <select value={newEvidenceId || ""} onChange={(event) => setNewEvidenceId(Number(event.target.value))}>
              <option value="">Select Evidence</option>
              {evidenceQuery.data?.map((item) => (
                <option key={item.id} value={item.id}>
                  #{item.id} - {item.title}
                </option>
              ))}
            </select>
            <Button
              onClick={() =>
                createItemMutation.mutate({
                  caseId: selectedCaseId,
                  payload: {
                    item_type: "EVIDENCE_REF",
                    evidence: newEvidenceId,
                    title: `Evidence ${newEvidenceId}`,
                    x: 80,
                    y: 80,
                  },
                })
              }
              disabled={!selectedCaseId || !newEvidenceId}
            >
              Add Evidence Node
            </Button>
          </div>

          <div className="divider" />
          <h2>Items</h2>
          {boardItems.length === 0 && <EmptyState title="No Board Items" description="Create a note or evidence node to start." />}
          <div className="stack-list">
            {boardItems.map((item) => (
              <div key={item.id} className="queue-item">
                <strong>
                  #{item.id} {item.title || toTitleCase(item.item_type)}
                </strong>
                <div className="button-row">
                  <Button
                    variant="secondary"
                    onClick={() =>
                      patchItemMutation.mutate({
                        itemId: item.id,
                        payload: { title: `${item.title || "Node"} (updated)` },
                      })
                    }
                  >
                    Rename
                  </Button>
                  <Button variant="danger" onClick={() => deleteItemMutation.mutate(item.id)}>
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h2>Board Canvas</h2>
          {selectedCaseId === 0 && <EmptyState title="No Case Selected" description="Select a case to load detective board data." />}
          {selectedCaseId > 0 && boardQuery.isLoading && <Skeleton style={{ height: "20rem" }} />}
          {selectedCaseId > 0 && (
            <div className="board-canvas-wrapper" ref={boardRef}>
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onNodeDragStop={(_, node) => {
                  patchItemMutation.mutate({
                    itemId: Number(node.id),
                    payload: { x: node.position.x, y: node.position.y },
                  });
                }}
                fitView
              >
                <Background gap={18} size={1} />
                <MiniMap />
                <Controls />
              </ReactFlow>
            </div>
          )}
          {boardConnections.length > 0 && (
            <div className="stack-list">
              <h3>Connections</h3>
              {boardConnections.map((connection) => (
                <div key={connection.id} className="queue-item">
                  <span>
                    #{connection.id}: {connection.from_item}
                    {" -> "}
                    {connection.to_item}
                  </span>
                  <Button variant="danger" onClick={() => deleteConnectionMutation.mutate(connection.id)}>
                    Remove Link
                  </Button>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </section>
  );
}
