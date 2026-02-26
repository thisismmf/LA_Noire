import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorAlert } from "../components/ui/ErrorAlert";
import { Skeleton } from "../components/ui/Skeleton";
import { extractApiError } from "../utils/errors";
import { toTitleCase } from "../utils/format";
import { assignRole, createRole, deleteRole, listRoles, listUsers, removeRole, updateRole } from "./adminApi";

export function AdminPanelPage() {
  const queryClient = useQueryClient();
  const [newRole, setNewRole] = useState({ name: "", slug: "", description: "" });
  const [filters, setFilters] = useState({ username: "", national_id: "", role: "" });
  const [appliedFilters, setAppliedFilters] = useState({ username: "", national_id: "", role: "" });
  const [assignmentForm, setAssignmentForm] = useState({ user_id: 0, role_id: 0 });
  const [message, setMessage] = useState("");

  const rolesQuery = useQuery({
    queryKey: ["roles"],
    queryFn: listRoles,
  });

  const usersQuery = useQuery({
    queryKey: ["users", appliedFilters],
    queryFn: () => listUsers(appliedFilters),
  });

  const createRoleMutation = useMutation({
    mutationFn: createRole,
    onSuccess: () => {
      setMessage("Role created.");
      setNewRole({ name: "", slug: "", description: "" });
      queryClient.invalidateQueries({ queryKey: ["roles"] });
    },
    onError: (error) => setMessage(extractApiError(error)),
  });

  const updateRoleMutation = useMutation({
    mutationFn: ({ roleId, payload }: { roleId: number; payload: Partial<{ name: string; slug: string; description: string }> }) =>
      updateRole(roleId, payload),
    onSuccess: () => {
      setMessage("Role updated.");
      queryClient.invalidateQueries({ queryKey: ["roles"] });
    },
    onError: (error) => setMessage(extractApiError(error)),
  });

  const deleteRoleMutation = useMutation({
    mutationFn: deleteRole,
    onSuccess: () => {
      setMessage("Role deleted.");
      queryClient.invalidateQueries({ queryKey: ["roles"] });
    },
    onError: (error) => setMessage(extractApiError(error)),
  });

  const assignRoleMutation = useMutation({
    mutationFn: ({ userId, roleId }: { userId: number; roleId: number }) => assignRole(userId, { role_id: roleId }),
    onSuccess: () => {
      setMessage("Role assigned to user.");
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (error) => setMessage(extractApiError(error)),
  });

  const removeRoleMutation = useMutation({
    mutationFn: ({ userId, roleId }: { userId: number; roleId: number }) => removeRole(userId, { role_id: roleId }),
    onSuccess: () => {
      setMessage("Role removed from user.");
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (error) => setMessage(extractApiError(error)),
  });

  return (
    <section className="page">
      <h1>Admin Panel</h1>
      <p>Manage roles and user role assignment without code changes, matching the dynamic RBAC requirement.</p>
      <ErrorAlert message={message} />

      <div className="cards-grid">
        <Card>
          <h2>Role Management</h2>
          <form
            className="form-grid"
            onSubmit={(event) => {
              event.preventDefault();
              createRoleMutation.mutate(newRole);
            }}
          >
            <label>
              Name
              <input value={newRole.name} onChange={(event) => setNewRole((prev) => ({ ...prev, name: event.target.value }))} required />
            </label>
            <label>
              Slug
              <input value={newRole.slug} onChange={(event) => setNewRole((prev) => ({ ...prev, slug: event.target.value }))} required />
            </label>
            <label>
              Description
              <textarea
                value={newRole.description}
                onChange={(event) => setNewRole((prev) => ({ ...prev, description: event.target.value }))}
              />
            </label>
            <Button type="submit" disabled={createRoleMutation.isPending}>
              Create Role
            </Button>
          </form>

          <div className="divider" />
          <h3>Role List</h3>
          {rolesQuery.isLoading && <Skeleton style={{ height: "3rem" }} />}
          {rolesQuery.data?.length === 0 && <EmptyState title="No Roles" description="No roles returned from API." />}
          <div className="stack-list">
            {rolesQuery.data?.map((role) => (
              <div key={role.id} className="queue-item">
                <div>
                  <strong>{role.name}</strong>
                  <p className="muted-text">
                    {role.slug} | {role.is_system ? "System Role" : "Custom Role"}
                  </p>
                  <p>{role.description || "-"}</p>
                </div>
                {!role.is_system && (
                  <div className="button-row wrap">
                    <Button
                      variant="secondary"
                      onClick={() =>
                        updateRoleMutation.mutate({
                          roleId: role.id,
                          payload: { description: `${role.description || "Custom role"} (updated)` },
                        })
                      }
                    >
                      Quick Update
                    </Button>
                    <Button variant="danger" onClick={() => deleteRoleMutation.mutate(role.id)}>
                      Delete
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h2>User Access Management</h2>
          <div className="inline-form">
            <input
              placeholder="Username"
              value={filters.username}
              onChange={(event) => setFilters((prev) => ({ ...prev, username: event.target.value }))}
            />
            <input
              placeholder="National ID"
              value={filters.national_id}
              onChange={(event) => setFilters((prev) => ({ ...prev, national_id: event.target.value }))}
            />
            <input placeholder="Role slug" value={filters.role} onChange={(event) => setFilters((prev) => ({ ...prev, role: event.target.value }))} />
            <Button variant="secondary" onClick={() => setAppliedFilters(filters)}>
              Search
            </Button>
          </div>

          <div className="divider" />
          <h3>Assign or Remove Role</h3>
          <div className="inline-form">
            <input
              type="number"
              min={0}
              placeholder="User ID"
              value={assignmentForm.user_id || ""}
              onChange={(event) => setAssignmentForm((prev) => ({ ...prev, user_id: Number(event.target.value) }))}
            />
            <select
              value={assignmentForm.role_id || ""}
              onChange={(event) => setAssignmentForm((prev) => ({ ...prev, role_id: Number(event.target.value) }))}
            >
              <option value="">Select Role</option>
              {rolesQuery.data?.map((role) => (
                <option key={role.id} value={role.id}>
                  #{role.id} {toTitleCase(role.slug)}
                </option>
              ))}
            </select>
            <Button
              onClick={() => assignRoleMutation.mutate({ userId: assignmentForm.user_id, roleId: assignmentForm.role_id })}
              disabled={!assignmentForm.user_id || !assignmentForm.role_id}
            >
              Assign
            </Button>
            <Button
              variant="danger"
              onClick={() => removeRoleMutation.mutate({ userId: assignmentForm.user_id, roleId: assignmentForm.role_id })}
              disabled={!assignmentForm.user_id || !assignmentForm.role_id}
            >
              Remove
            </Button>
          </div>

          <div className="divider" />
          <h3>User Directory</h3>
          {usersQuery.isLoading && <Skeleton style={{ height: "4rem" }} />}
          {usersQuery.data?.length === 0 && <EmptyState title="No Users" description="No users matched current filters." />}
          <div className="stack-list">
            {usersQuery.data?.map((user) => (
              <div key={user.id} className="queue-item">
                <div>
                  <strong>
                    #{user.id} {user.username}
                  </strong>
                  <p className="muted-text">
                    {user.first_name} {user.last_name} | {user.national_id}
                  </p>
                  <p>{user.email}</p>
                </div>
                <div className="chip-row">
                  {(user.roles || []).map((role) => (
                    <span key={`${user.id}-${role}`} className="role-chip">
                      {role}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </section>
  );
}
