// utils/format.js
export const formatUSD = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  // utils/format.js
export const formatZIG = (amount) => {
    return `ZIG ${Number(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}`;
  };