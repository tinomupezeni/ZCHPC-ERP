import React from "react";
import { BookOpen, Clock, Folder, Edit2, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export interface TrainingProgram {
  id: number;
  title: string;
  category: string;
  duration: string;
  mandatory: boolean;
}

interface Props {
  program: TrainingProgram;
  onEdit: (id: number) => void;
  onDelete: (id: number) => void;
}

export function TrainingProgramCard({ program, onEdit, onDelete }: Props) {
  return (
    <Card className="hover:shadow-md transition-shadow duration-300">
      <CardHeader className="flex items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-blue-600" aria-hidden />
          <span className="font-semibold">{program.title}</span>
          {program.mandatory && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              Mandatory
            </span>
          )}
        </CardTitle>
        <div className="flex gap-2">
          {/* Edit Button (Blue) */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => onEdit(program.id)}
            className="transition-all duration-200 hover:scale-[1.02] gap-1 text-blue-600 border-blue-200 hover:bg-blue-50"
          >
            <Edit2 className="w-4 h-4" />
            <span>Edit</span>
          </Button>
          {/* Delete Button (Red) */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => onDelete(program.id)}
            className="transition-all duration-200 hover:scale-[1.02] gap-1 text-red-600 border-red-200 hover:bg-red-50"
          >
            <Trash2 className="w-4 h-4" />
            <span>Delete</span>
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <Folder className="w-4 h-4 text-gray-500" />
            <span><b>Category:</b> {program.category}</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-gray-500" />
            <span><b>Duration:</b> {program.duration}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}