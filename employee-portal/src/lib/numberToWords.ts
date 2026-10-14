/**
 * Converts a numeric amount to words (e.g. 50 -> "Fifty litres")
 */
export function numberToWords(num: number): string {
  if (!Number.isFinite(num) || num <= 0) return '';
  const ones = [
    '', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
    'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
    'Seventeen', 'Eighteen', 'Nineteen'
  ];
  const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];

  const convertWhole = (n: number): string => {
    if (n === 0) return '';
    if (n < 20) return ones[n];
    if (n < 100) return `${tens[Math.floor(n / 10)]}${n % 10 !== 0 ? `-${ones[n % 10].toLowerCase()}` : ''}`;
    if (n < 1000) return `${ones[Math.floor(n / 100)]} hundred${n % 100 !== 0 ? ` and ${convertWhole(n % 100).toLowerCase()}` : ''}`;
    if (n < 1000000) return `${convertWhole(Math.floor(n / 1000))} thousand${n % 1000 !== 0 ? ` ${convertWhole(n % 1000).toLowerCase()}` : ''}`;
    return String(n);
  };

  const whole = Math.floor(num);
  const decimal = Math.round((num - whole) * 100);
  const wholeWords = convertWhole(whole) || 'Zero';

  if (decimal > 0) {
    return `${wholeWords} point ${convertWhole(decimal).toLowerCase()} litres`;
  }
  return `${wholeWords} litres`;
}

