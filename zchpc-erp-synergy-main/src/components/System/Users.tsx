import React, { useState } from "react";
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
import { UserPlus, Search, Edit, Trash2, User as UserIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns"; 
import {deleteUserMethod} from '@/services/hr.services'

export default function Users({ setAddUser, users }) {
  const [searchTerm, setSearchTerm] = useState("");

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

  const Modal = (id) => {
    // Use UUID for editing
    console.log("Edit UUID:", id);
    // setEditEmployeeId(id); 
    // setEditUserModal(true);
  };

  const deleteUser = (id) => {
    // Use UUID for deletion
    deleteUserMethod(id)
      .then(() => {
        toast.success("User deleted successfully");
        // Ideally refresh the list from parent or context here
      })
      .catch((error) => {
        console.log(error);
        toast.error("Error deleting user");
      });
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
                      <TableCell>{getStatusBadge(user.is_active)}</TableCell>
                      
                      <TableCell className="text-right">
                        <div className="flex justify-end space-x-1">
                          {/* 8. Pass UUID to actions */}
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => Modal(user.id)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => deleteUser(user.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
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