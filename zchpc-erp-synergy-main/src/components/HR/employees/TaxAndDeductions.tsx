import { useState, useEffect } from "react";
import { Check, ChevronsUpDown, Plus, Loader } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { cn } from "@/lib/utils";
import { getDeductionTypes, addDeductionType } from "@/services/hr.services";
import { toast } from "sonner";

export default function TaxAndDeductionsDropdown({ onSelect }) {
  const [open, setOpen] = useState(false);
  const [selectedItems, setSelectedItems] = useState([]);
  const [items, setItems] = useState([]);
  
  // Creation State
  const [searchValue, setSearchValue] = useState("");
  const [creating, setCreating] = useState(false);

  const loadItems = async () => {
    try {
      const data = await getDeductionTypes();
      setItems(data);
    } catch (error) {
      console.error("Failed to load deductions", error);
    }
  };

  useEffect(() => { loadItems(); }, []);

  const handleSelect = (item) => {
    const exists = selectedItems.find((i) => i.id === item.id);
    let newSelection;
    
    if (exists) {
      newSelection = selectedItems.filter((i) => i.id !== item.id);
    } else {
      // Default amount 0, editable later
      newSelection = [...selectedItems, { id: item.id, name: item.name, amount: 0 }];
    }
    
    setSelectedItems(newSelection);
    onSelect(newSelection);
  };

  const handleCreate = async () => {
    if (!searchValue.trim()) return;
    setCreating(true);
    try {
      const newDeduction = await addDeductionType({ name: searchValue });
      toast.success(`Created ${newDeduction.name}`);
      
      // Add to local list immediately
      setItems((prev) => [...prev, newDeduction]);
      
      // Automatically select it
      handleSelect(newDeduction);
      
      // Clear search
      setSearchValue("");
    } catch (error) {
      toast.error("Failed to create deduction type");
    } finally {
      setCreating(false);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between text-left font-normal h-auto min-h-[40px]"
        >
          {selectedItems.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {selectedItems.map((item) => (
                <span key={item.id} className="bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded-full flex items-center gap-1">
                  {item.name}
                  <span 
                    className="cursor-pointer hover:text-blue-900 font-bold"
                    onClick={(e) => {
                        e.stopPropagation(); // Prevent toggling popover
                        handleSelect(item); // Deselect
                    }}
                  >×</span>
                </span>
              ))}
            </div>
          ) : (
            <span className="text-muted-foreground">Select taxes & deductions...</span>
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-0" align="start">
        <Command>
          <CommandInput 
            placeholder="Search or create deduction..." 
            onValueChange={setSearchValue}
          />
          <CommandList>
            <CommandEmpty className="py-2 px-4 text-sm">
               {creating ? (
                 <div className="flex items-center gap-2 text-blue-600">
                    <Loader className="h-4 w-4 animate-spin"/> Creating...
                 </div>
               ) : (
                 <button 
                   onClick={handleCreate}
                   className="flex items-center gap-2 text-blue-600 hover:underline font-medium w-full text-left"
                 >
                    <Plus className="h-4 w-4"/> Create "{searchValue}"
                 </button>
               )}
            </CommandEmpty>
            <CommandGroup heading="Available Deductions">
              {items.map((item) => (
                <CommandItem
                  key={item.id}
                  value={item.name}
                  onSelect={() => handleSelect(item)}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      selectedItems.find((i) => i.id === item.id) ? "opacity-100" : "opacity-0"
                    )}
                  />
                  {item.name}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}