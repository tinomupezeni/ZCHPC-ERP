const PayrollSummaryCard = ({
  title,
  value,
  secondaryValue,
  icon,
  color,
  subtitle,
}) => {
  const colorClasses = {
    blue: "bg-blue-50 border-blue-100 text-blue-800",
    green: "bg-green-50 border-green-100 text-green-800",
    red: "bg-red-50 border-red-100 text-red-800",
    purple: "bg-purple-50 border-purple-100 text-purple-800",
  };

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color]}`}>
      <div className="flex justify-between">
        <div>
          <div className="text-sm font-medium">{title}</div>
          {subtitle && <div className="text-xs opacity-70">{subtitle}</div>}
        </div>
        {icon}
      </div>
      <div className="mt-2 text-2xl font-bold">{value}</div>
      {secondaryValue && (
        <div className="mt-1 text-sm opacity-70">{secondaryValue}</div>
      )}
    </div>
  );
};

export default PayrollSummaryCard;
