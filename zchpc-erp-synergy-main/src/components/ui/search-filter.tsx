interface SearchFilterBarProps {
  search: string;
  onSearchChange: (val: string) => void;
  categories: string[];
  selectedCategory: string;
  onCategoryChange: (val: string) => void;
}

export function SearchFilterBar({
  search,
  onSearchChange,
  categories,
  selectedCategory,
  onCategoryChange,
}: SearchFilterBarProps) {
  return (
    <div className="flex flex-col md:flex-row items-stretch md:items-center gap-2">
      <input
        className="border rounded px-2 py-1 text-sm"
        type="text"
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        placeholder="Search by title or category..."
        aria-label="search training programs"
      />
      <select
        className="border rounded px-2 py-1 text-sm"
        value={selectedCategory}
        onChange={(e) => onCategoryChange(e.target.value)}
        aria-label="filter by category"
      >
        {categories.map(c => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>
    </div>
  );
}
