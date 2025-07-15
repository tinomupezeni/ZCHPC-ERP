import React from "react";
import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
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
import { UserPlus, Search, Edit, Trash2, User, Badge } from "lucide-react";

export default function Users({setAddUser}) {
  const [users, setUsers] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  
   const getStatusBadge = (status: boolean) => {
      switch (status) {
        case true:
          return (
            <Badge className="bg-green-100 text-green-800 hover:bg-green-200">
              Active
            </Badge>
          );
        case false:
          return (
            <Badge className="bg-gray-100 text-gray-800 hover:bg-gray-200">
              Inactive
            </Badge>
          );
        case null:
          return (
            <Badge className="bg-red-100 text-red-800 hover:bg-red-200">
              Suspended
            </Badge>
          );
        default:
          return <Badge>{status}</Badge>;
      }
    };
  
    const addNewUser = () => {
      toast.success("User creation form would open here");
      setAddUser(true);
    };
  
    const Modal = (id: string) => {
      toast.success(`Edit user ${id}`);
      setEditEmployeeId(id)
      setEditUserModal(true);
    };
  
    const deleteUser = (id: string) => {
      Server.deleteUser(id)
        .then(() => {
          toast.success(`Deleted employee ${id}`);
          setUsers(users.filter((user) => user.employeeid !== id));
        })
        .catch((error) => {
          console.log(error);
  
          toast.error("Error deleting user ", id);
        });
    };
  

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
                  <TableHead className="w-[80px]">ID</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Last Active</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.length > 0 ? (
                  users.map((user) => (
                    <TableRow key={user.employeeid}>
                      <TableCell className="font-medium">
                        {user.employeeid}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Avatar className="h-8 w-8">
                            <AvatarImage
                              src={`https://api.dicebear.com/7.x/initials/svg?seed=${user.firstname} ${user.surname}`}
                              alt={`${user.firstname} ${user.surname}`}
                            />
                            <AvatarFallback>
                              {`${user.firstname} ${user.surname}`.charAt(0)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-medium">{`${user.firstname} ${user.surname}`}</div>
                            <div className="text-sm text-muted-foreground">
                              {user.email}
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{user.role}</TableCell>
                      <TableCell>{user.department}</TableCell>
                      <TableCell>{user.lastActive}</TableCell>
                      <TableCell>{getStatusBadge(user.isActive)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end space-x-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => Modal(user.employeeid)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => deleteUser(user.employeeid)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan={7}
                      className="py-10 text-center text-muted-foreground"
                    >
                      <div className="flex flex-col items-center space-y-2">
                        <User className="h-8 w-8 text-gray-400" />
                        <p className="text-lg font-medium">
                          No system users yet
                        </p>
                        <p className="text-sm text-gray-500">
                          Add a user to get started
                        </p>
                        <Button variant="outline" onClick={addNewUser}>
                          <UserPlus /> Add User
                        </Button>
                      </div>
                    </td>
                  </tr>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
