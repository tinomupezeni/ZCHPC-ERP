import { useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Receipt, Upload, X, Loader2 } from 'lucide-react';
import { format } from 'date-fns';
import type { ExpenseCategory, CreateExpenseClaimData, ExpenseCurrency } from '@/types/expense.types';

interface ExpenseFormProps {
  categories: ExpenseCategory[];
  onSubmit: (data: CreateExpenseClaimData) => Promise<void>;
  isSubmitting: boolean;
}

export function ExpenseForm({
  categories,
  onSubmit,
  isSubmitting,
}: ExpenseFormProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState<string>('');
  const [amount, setAmount] = useState<string>('');
  const [currency, setCurrency] = useState<ExpenseCurrency>('USD');
  const [dateIncurred, setDateIncurred] = useState<string>('');
  const [receipt, setReceipt] = useState<File | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const fileInputRef = useRef<HTMLInputElement>(null);
  const today = format(new Date(), 'yyyy-MM-dd');

  const selectedCategory = categories.find((c) => c.id === parseInt(category));

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!title.trim()) {
      newErrors.title = 'Title is required';
    }

    if (!category) {
      newErrors.category = 'Please select a category';
    }

    if (!amount || parseFloat(amount) <= 0) {
      newErrors.amount = 'Please enter a valid amount';
    }

    if (selectedCategory?.max_amount && parseFloat(amount) > selectedCategory.max_amount) {
      newErrors.amount = `Amount exceeds maximum (${selectedCategory.max_amount}) for this category`;
    }

    if (!dateIncurred) {
      newErrors.dateIncurred = 'Please select a date';
    }

    if (selectedCategory?.requires_receipt && !receipt) {
      newErrors.receipt = 'A receipt is required for this category';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    await onSubmit({
      title: title.trim(),
      description: description.trim() || undefined,
      category: parseInt(category),
      amount: parseFloat(amount),
      currency,
      date_incurred: dateIncurred,
      receipt: receipt || undefined,
    });

    // Reset form
    setTitle('');
    setDescription('');
    setCategory('');
    setAmount('');
    setCurrency('USD');
    setDateIncurred('');
    setReceipt(null);
    setErrors({});
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
      if (!allowedTypes.includes(file.type)) {
        setErrors({ ...errors, receipt: 'Please upload an image (JPG, PNG, GIF) or PDF' });
        return;
      }
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setErrors({ ...errors, receipt: 'File size must be less than 5MB' });
        return;
      }
      setReceipt(file);
      setErrors({ ...errors, receipt: '' });
    }
  };

  const removeReceipt = () => {
    setReceipt(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Receipt className="h-5 w-5" />
          New Expense Claim
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              placeholder="e.g., Office supplies purchase"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            {errors.title && (
              <p className="text-sm text-destructive">{errors.title}</p>
            )}
          </div>

          {/* Category */}
          <div className="space-y-2">
            <Label htmlFor="category">Category</Label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger id="category">
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((cat) => (
                  <SelectItem key={cat.id} value={cat.id.toString()}>
                    {cat.name}
                    {cat.max_amount && (
                      <span className="text-muted-foreground ml-2">
                        (max ${cat.max_amount})
                      </span>
                    )}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.category && (
              <p className="text-sm text-destructive">{errors.category}</p>
            )}
            {selectedCategory?.description && (
              <p className="text-xs text-muted-foreground">{selectedCategory.description}</p>
            )}
          </div>

          {/* Amount and Currency */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="amount">Amount</Label>
              <Input
                id="amount"
                type="number"
                step="0.01"
                min="0.01"
                placeholder="0.00"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
              {errors.amount && (
                <p className="text-sm text-destructive">{errors.amount}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="currency">Currency</Label>
              <Select value={currency} onValueChange={(v) => setCurrency(v as ExpenseCurrency)}>
                <SelectTrigger id="currency">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="USD">USD</SelectItem>
                  <SelectItem value="ZiG">ZiG</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Date Incurred */}
          <div className="space-y-2">
            <Label htmlFor="dateIncurred">Date Incurred</Label>
            <Input
              id="dateIncurred"
              type="date"
              max={today}
              value={dateIncurred}
              onChange={(e) => setDateIncurred(e.target.value)}
            />
            {errors.dateIncurred && (
              <p className="text-sm text-destructive">{errors.dateIncurred}</p>
            )}
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description (Optional)</Label>
            <Textarea
              id="description"
              placeholder="Additional details about this expense..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>

          {/* Receipt Upload */}
          <div className="space-y-2">
            <Label>
              Receipt
              {selectedCategory?.requires_receipt && (
                <span className="text-destructive ml-1">*</span>
              )}
            </Label>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*,.pdf"
              onChange={handleFileChange}
              className="hidden"
            />
            {receipt ? (
              <div className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg">
                <Receipt className="h-5 w-5 text-muted-foreground" />
                <span className="flex-1 text-sm truncate">{receipt.name}</span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={removeReceipt}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload Receipt
              </Button>
            )}
            {errors.receipt && (
              <p className="text-sm text-destructive">{errors.receipt}</p>
            )}
            <p className="text-xs text-muted-foreground">
              Accepted formats: JPG, PNG, GIF, PDF (max 5MB)
            </p>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              'Create Expense Claim'
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

export default ExpenseForm;
