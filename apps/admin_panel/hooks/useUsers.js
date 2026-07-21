import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { userService } from "../services/userService";

export function useUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [isBlocked, setIsBlocked] = useState("");

const fetchUsers = useCallback(async () => {
  setLoading(true);
  try {
    const params = { page };
    if (search) params.search = search;
    if (role) params.role = role;
    if (isBlocked !== "") params.is_blocked = isBlocked;

    const res = await userService.list(params);
    setUsers(res.data.data.results);
    setTotalCount(res.data.data.count);
  } catch (err) {
    toast.error(err.response?.data?.message || "Failed to load users.");
  } finally {
    setLoading(false);
  }
}, [page, search, role, isBlocked]);

  const axios_safe_get = async (params) => {
    return userService.list(params);
  };

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const changeRole = async (id, newRole) => {
    try {
      await userService.updateRole(id, newRole);
      toast.success("User role updated successfully.");
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.message || "Failed to update role.");
    }
  };

  const toggleBlock = async (id) => {
    try {
      const res = await userService.toggleBlock(id);
      toast.success(res.data.message);
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.message || "Failed to update user status.");
    }
  };

  const deleteUser = async (id) => {
    try {
      await userService.delete(id);
      toast.success("User deleted successfully.");
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.message || "Failed to delete user.");
    }
  };

  return {
    users,
    loading,
    page,
    setPage,
    totalCount,
    search,
    setSearch,
    role,
    setRole,
    isBlocked,
    setIsBlocked,
    changeRole,
    toggleBlock,
    deleteUser,
    refresh: fetchUsers,
  };
}