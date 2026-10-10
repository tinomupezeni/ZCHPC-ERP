import React, { useRef, useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { toast } from "sonner";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { UserPlus, Search, Edit, UserX, Unlock, User as UserIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";
import { deactivateUser } from '@/services/hr.services'
import { unlockUser } from '@/services/auth.services'
import { NO_PERMISSION, readApiError } from '@/lib/apiErrors'

// What the user is told when deactivation is refused, by the backend's code.
const DEACTIVATE_REFUSALS: Record<string, string> = {
  EMPLOYEE_DEACTIVATE_NOT_AUTHORIZED: "You don't have permission to deactivate user accounts.",
  EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY: "You don't have permission to deactivate this user.",
  EMPLOYEE_SELF_DEACTIVATION: "You can't deactivate your own account.",
  EMPLOYEE_ARCHIVED: "This employee has been archived, so their account can't be changed.",
};

// Locked by failed logins until lockout_until (cleared by unlock).
const isLocked = (user) =>
  !!user.lockout_until && new Date(user.lockout_until) > new Date();

export default function Users({ setAddUser, users, onUsersChanged, onEditUser }) {
  const [searchTerm, setSearchTerm] = useState("");
  // The user whose deactivation is in flight; one request per action.
  const [deactivatingId, setDeactivatingId] = useState(null);
  const deactivating = useRef(false);
  const [unlockingId, setUnlockingId] = useState(null);

  // 1. Fixed Status Logic (Handle 'is_active')
  const getStatusBadge = (isActive) => {
    if (isActive === true) {
        return <Badge className="bg-green-100 text-green-800 hover:bg-green-200">Active</Badge>;
    } else {
        return <Badge className="bg-gray-100 text-gray-800 hover:bg-gray-200">Inactive</Badge>;
    }
  };

  const addNewUser = () => {
    setAddUser(true);
  };

  const handleUnlock = async (user) => {
    if (unlockingId !== null) return;
    const name = `${user.first_name || ""} ${user.last_name || ""}`.trim() || user.email;
    setUnlockingId(user.id);
    try {
      await unlockUser(user.id);
      toast.success(`${name} can sign in again.`);
      onUsersChanged?.();
    } catch (error) {
      const { status } = readApiError(error);
      if (status === 403) {
        toast.error("You don't have permission to unlock this account.");
      } else if (status === 404) {
        toast.error(`${name}'s account no longer exists. The list has been refreshed.`);
        onUsersChanged?.();
      } else {
        toast.error(`We couldn't unlock ${name}. Please try again.`);
      }
    } finally {
      setUnlockingId(null);
    }
  };

  // Users are never deleted (AUD-02); deactivating ends their access and can
  // be reversed. The backend decides who may deactivate whom.
  const handleDeactivate = async (user) => {
    if (deactivating.current) return;
    const name = `${user.first_name || ""} ${user.last_name || ""}`.trim() || user.email;
    if (!confirm(`Deactivate ${name}? They will no longer be able to sign in. The account can be reactivated later.`)) {
      return;
    }

    deactivating.current = true;
    setDeactivatingId(user.id);
    try {
      await deactivateUser(user.id);
      toast.success(`${name} has been deactivated.`);
      onUsersChanged?.();
    } catch (error) {
      const { status, code } = readApiError(error);
      if (status === 404) {
        toast.error(`${name}'s account no longer exists. The list has been refreshed.`);
        onUsersChanged?.();
      } else if (code && DEACTIVATE_REFUSALS[code]) {
        toast.error(DEACTIVATE_REFUSALS[code]);
      } else if (status === 403) {
        toast.error(NO_PERMISSION);
      } else {
        toast.error(`We couldn't deactivate ${name}. Please try again.`);
      }
    } finally {
      deactivating.current = false;
      setDeactivatingId(null);
    }
  };

  // Filter logic updated to check first_name, last_name and email
  const filteredUsers = users.filter(user => 
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.first_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.last_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div>
      <Card className="subtle-shadow">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0 pb-2">
          <CardTitle>User Management</CardTitle>
          <div className="flex items-center space-x-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search users..."
                className="pl-8 w-[200px] md:w-[250px]"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Button onClick={addNewUser}>
              <UserPlus className="mr-2 h-4 w-4" />
              Add User
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">Emp ID</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.length > 0 ? (
                  filteredUsers.map((user) => (
                    // 2. Use UUID (user.id) for the React Key
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">
                        {/* 3. Access Nested Employee ID safely */}
                        {user.employee_profile?.employee_id || "N/A"}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Avatar className="h-8 w-8">
                            {/* 4. Fix Name Accessors */}
                            <AvatarImage
                              src={`https://api.dicebear.com/7.x/initials/svg?seed=${user.first_name} ${user.last_name}`}
                              alt={`${user.first_name} ${user.last_name}`}
                            />
                            <AvatarFallback>
                              {user.first_name ? user.first_name.charAt(0) : "U"}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-medium">
                                {user.first_name} {user.last_name}
                            </div>
                            <div className="text-sm text-muted-foreground lowercase">
                              {user.email}
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      
                      {/* 5. Access Nested Profile Data */}
                      <TableCell>
                        {user.employee_profile?.role || (user.is_superuser ? "Superuser" : "User")}
                      </TableCell>
                      <TableCell>
                        {user.employee_profile?.department || "-"}
                      </TableCell>
                      
                      {/* 6. Date Formatting */}
                      <TableCell>
                        {user.date_joined
                          ? format(new Date(user.date_joined), "PP") 
                          : "-"}
                      </TableCell>
                      
                      {/* 7. Status Fix */}
                      <TableCell>
                        {getStatusBadge(user.is_active)}
                        {isLocked(user) && (
                          <Badge className="ml-1 bg-amber-100 text-amber-800 hover:bg-amber-200">Locked</Badge>
                        )}
                      </TableCell>
                      
                      <TableCell className="text-right">
                        <div className="flex justify-end space-x-1">
                          {/* 8. Pass UUID to actions */}
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Edit"
                            onClick={() => onEditUser?.(user.id)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          {isLocked(user) && (
                            <Button
                              variant="ghost"
                              size="sm"
                              title="Unlock"
                              disabled={unlockingId !== null}
                              onClick={() => handleUnlock(user)}
                            >
                              <Unlock className="mr-1 h-4 w-4" />
                              {unlockingId === user.id ? "Unlocking..." : "Unlock"}
                            </Button>
                          )}
                          {user.is_active && (
                            <Button
                              variant="ghost"
                              size="sm"
                              title="Deactivate"
                              disabled={deactivatingId !== null}
                              onClick={() => handleDeactivate(user)}
                            >
                              <UserX className="mr-1 h-4 w-4" />
                              {deactivatingId === user.id ? "Deactivating..." : "Deactivate"}
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell
                      colSpan={7}
                      className="py-10 text-center text-muted-foreground"
                    >
                      <div className="flex flex-col items-center space-y-2">
                        <UserIcon className="h-8 w-8 text-gray-400" />
                        <p className="text-lg font-medium">
                          No users found
                        </p>
                        <Button variant="outline" onClick={addNewUser}>
                          <UserPlus className="mr-2 h-4 w-4" /> Add User
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}