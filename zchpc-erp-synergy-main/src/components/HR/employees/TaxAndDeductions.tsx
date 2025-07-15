import { useState } from "react";
import { ChevronDown } from "lucide-react";

const TaxAndDeductionsDropdown = ({ onSelect }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedItems, setSelectedItems] = useState([]);

  const mandatoryDeductions = [
    { id: "paye", name: "PAYE (Pay As You Earn)", rate: "Progressive (0-40%)" },
    { id: "nssa_pension", name: "NSSA Pension (4.5%)", rate: "4.5% of pensionable salary" },
    { id: "aids_levy", name: "AIDS Levy (3%)", rate: "3% of taxable income" },
    { id: "withholding_tax", name: "ZIMRA Withholding Tax", rate: "Varies by benefit" }
  ];

  const optionalDeductions = [
    { 
      category: "Medical Aid", 
      options: [
        { id: "cimas", name: "CIMAS Medical Aid" },
        { id: "first_mutual_health", name: "First Mutual Health" },
        { id: "psmas", name: "PSMAS" },
        { id: "alliance_health", name: "Alliance Health" }
      ]
    },
    { 
      category: "Pension Funds", 
      options: [
        { id: "old_mutual", name: "Old Mutual Pension" },
        { id: "first_mutual_pension", name: "First Mutual Pension" },
        { id: "cbz_pension", name: "CBZ Pension Fund" }
      ]
    },
    { 
      category: "Insurance", 
      options: [
        { id: "funeral_cover", name: "Funeral Cover" },
        { id: "life_insurance", name: "Life Insurance" },
        { id: "disability_insurance", name: "Disability Insurance" }
      ]
    },
    { 
      category: "Union Dues", 
      options: [
        { id: "zimta", name: "ZIMTA (Teachers)" },
        { id: "zctu", name: "ZCTU Affiliate" }
      ]
    }
  ];

  const toggleSelection = (item) => {
    const isSelected = selectedItems.some(selected => selected.id === item.id);
    if (isSelected) {
      setSelectedItems(selectedItems.filter(selected => selected.id !== item.id));
    } else {
      setSelectedItems([...selectedItems, item]);
    }
    onSelect([...selectedItems, item]);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex justify-between items-center w-full px-4 py-2 border border-gray-300 rounded-lg bg-white text-left"
      >
        <span>
          {selectedItems.length > 0 
            ? `${selectedItems.length} selected` 
            : "Select taxes and deductions"}
        </span>
        <ChevronDown className={`h-5 w-5 text-gray-400 transition-transform ${isOpen ? "transform rotate-180" : ""}`} />
      </button>

      {isOpen && (
        <div className="absolute z-10 mt-1 w-full bg-white shadow-lg rounded-lg border border-gray-200 max-h-96 overflow-y-auto">
          <div className="p-2 border-b">
            <h3 className="font-medium text-gray-800">Mandatory Deductions</h3>
            <div className="mt-1 space-y-1">
              {mandatoryDeductions.map(item => (
                <div key={item.id} className="flex items-center px-2 py-1">
                  <input
                    type="checkbox"
                    checked={selectedItems.some(selected => selected.id === item.id)}
                    onChange={() => toggleSelection(item)}
                    className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                    disabled // Mandatory items are disabled as they must be selected
                  />
                  <label className="ml-2 text-sm text-gray-700 w-full">
                    <div>{item.name}</div>
                    <div className="text-xs text-gray-500">{item.rate}</div>
                  </label>
                </div>
              ))}
            </div>
          </div>

          {optionalDeductions.map(group => (
            <div key={group.category} className="p-2 border-b">
              <h3 className="font-medium text-gray-800">{group.category}</h3>
              <div className="mt-1 space-y-1">
                {group.options.map(item => (
                  <div key={item.id} className="flex items-center px-2 py-1">
                    <input
                      type="checkbox"
                      checked={selectedItems.some(selected => selected.id === item.id)}
                      onChange={() => toggleSelection(item)}
                      className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                    />
                    <label className="ml-2 text-sm text-gray-700">{item.name}</label>
                  </div>
                ))}
              </div>
            </div>
          ))}

          <div className="p-2 flex justify-end">
            <button
              onClick={() => setIsOpen(false)}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaxAndDeductionsDropdown;