const PayrollStatusBadge = ({ status }) => {
    const baseClasses = "px-2 py-1 text-xs font-medium rounded-full";
    
    if (status === "Processed") {
      return <span className={`${baseClasses} bg-green-100 text-green-800`}>Processed</span>;
    }
    if (status === "Pending") {
      return <span className={`${baseClasses} bg-yellow-100 text-yellow-800`}>Pending</span>;
    }
    if (status === "Failed") {
      return <span className={`${baseClasses} bg-red-100 text-red-800`}>Failed</span>;
    }
    return <span className={`${baseClasses} bg-gray-100 text-gray-800`}>{status}</span>;
  };

  export default PayrollStatusBadge