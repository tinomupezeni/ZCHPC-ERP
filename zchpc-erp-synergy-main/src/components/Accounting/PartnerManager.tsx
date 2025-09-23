import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";

export default function PartnerManager() {
    const [partners, setPartners] = useState([]);
  
    useEffect(() => {
      axios.get("/api/partners/").then(res => setPartners(res.data));
    }, []);
  
    return (
      <div className="space-y-4">
        {/* <Button onClick={() => openModal("partner")}>Add Partner</Button> */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {partners.map(p => (
            <div key={p.id} className="p-4 border rounded shadow-sm">
              <p className="font-semibold">{p.name}</p>
              <p>Type: {p.partner_type}</p>
              <p>Currency: {p.currency?.code || "N/A"}</p>
              <div className="mt-2 flex space-x-2">
                <Button size="sm" variant="outline">Edit</Button>
                <Button size="sm" variant="destructive">Delete</Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }
  