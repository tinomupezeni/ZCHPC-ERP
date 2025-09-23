import { useEffect, useState } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";

export default function JournalEntries() {
    const [entries, setEntries] = useState([]);
  
    useEffect(() => {
      axios.get("/api/moves/").then(res => setEntries(res.data));
    }, []);
  
    return (
      <div className="space-y-4">
        {/* <Button onClick={() => openModal("journal-entry")}>New Journal Entry</Button> */}
        <div className="overflow-x-auto">
          <table className="w-full table-auto border-collapse border border-gray-200">
            <thead>
              <tr>
                <th className="border px-2 py-1">Date</th>
                <th className="border px-2 py-1">Ref</th>
                <th className="border px-2 py-1">Journal</th>
                <th className="border px-2 py-1">Posted</th>
                <th className="border px-2 py-1">Actions</th>
              </tr>
            </thead>
            <tbody>
              {entries.map(e => (
                <tr key={e.id}>
                  <td className="border px-2 py-1">{e.date}</td>
                  <td className="border px-2 py-1">{e.ref}</td>
                  <td className="border px-2 py-1">{e.journal.name}</td>
                  <td className="border px-2 py-1">{e.posted ? "Yes" : "No"}</td>
                  <td className="border px-2 py-1 flex space-x-2">
                    <Button size="sm">View</Button>
                    {!e.posted && <Button size="sm" variant="success">Post</Button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }
  