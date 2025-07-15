import React, { useState, useEffect } from 'react';
import { getTaxBrackets, createTaxBracket, updateTaxBracket, deleteTaxBracket } from '../server/api'; // Assuming 'api' is in 'src/api.js' based on previous example

const TaxConfig = () => {
    const [taxBrackets, setTaxBrackets] = useState([]);
    const [formData, setFormData] = useState({
        currency: 'USD',
        min_income: '',
        max_income: '',
        rate: '',
        deduction: '',
        active_from: new Date().toISOString().split('T')[0],
    });
    const [editingId, setEditingId] = useState(null);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        fetchTaxBrackets();
    }, []);

    const fetchTaxBrackets = async () => {
        try {
            const response = await getTaxBrackets({});
            setTaxBrackets(response.data.sort((a,b) => a.currency.localeCompare(b.currency) || a.min_income - b.min_income));
            setError('');
        } catch (err) {
            setError('Failed to fetch tax brackets.');
            console.error('Error fetching tax brackets:', err);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage('');
        setError('');
        try {
            const dataToSubmit = {
                ...formData,
                min_income: parseFloat(formData.min_income),
                max_income: formData.max_income ? parseFloat(formData.max_income) : null,
                rate: parseFloat(formData.rate),
                deduction: parseFloat(formData.deduction),
            };

            if (editingId) {
                await updateTaxBracket(editingId, dataToSubmit);
                setMessage('Tax bracket updated successfully!');
            } else {
                await createTaxBracket(dataToSubmit);
                setMessage('Tax bracket created successfully!');
                setFormData({
                    currency: 'USD',
                    min_income: '',
                    max_income: '',
                    rate: '',
                    deduction: '',
                    active_from: new Date().toISOString().split('T')[0],
                });
            }
            setEditingId(null);
            fetchTaxBrackets();
        } catch (err) {
            setError(`Failed to save tax bracket: ${err.response?.data ? JSON.stringify(err.response.data) : err.message}`);
            console.error('Error saving tax bracket:', err);
        }
    };

    const handleEdit = (bracket) => {
        setFormData({
            currency: bracket.currency,
            min_income: bracket.min_income,
            max_income: bracket.max_income || '',
            rate: bracket.rate,
            deduction: bracket.deduction,
            active_from: bracket.active_from,
        });
        setEditingId(bracket.id);
        setMessage('');
        setError('');
    };

    const handleDelete = async (id) => {
        if (window.confirm('Are you sure you want to delete this tax bracket?')) {
            setMessage('');
            setError('');
            try {
                await deleteTaxBracket(id);
                setMessage('Tax bracket deleted successfully!');
                fetchTaxBrackets();
            } catch (err) {
                setError('Failed to delete tax bracket.');
                console.error('Error deleting tax bracket:', err);
            }
        }
    };

    return (
        <div className="font-sans p-5 max-w-4xl mx-auto my-5 border border-gray-300 rounded-lg shadow-md bg-gray-50">
            <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Manage Tax Brackets</h2>
            {message && (
                <p className="text-green-700 bg-green-100 border border-green-200 p-3 rounded-md mb-4">
                    {message}
                </p>
            )}
            {error && (
                <p className="text-red-700 bg-red-100 border border-red-200 p-3 rounded-md mb-4">
                    {error}
                </p>
            )}

            <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8 p-5 border border-gray-200 rounded-md bg-white">
                <label className="block">
                    <span className="text-gray-700">Currency:</span>
                    <select
                        name="currency"
                        value={formData.currency}
                        onChange={handleChange}
                        required
                        className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    >
                        <option value="USD">USD</option>
                        <option value="ZWG">ZWL/ZiG</option>
                    </select>
                </label>
                <label className="block">
                    <span className="text-gray-700">Min Income:</span>
                    <input
                        type="number"
                        name="min_income"
                        value={formData.min_income}
                        onChange={handleChange}
                        step="0.01"
                        required
                        className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                </label>
                <label className="block">
                    <span className="text-gray-700">Max Income (Leave blank for highest):</span>
                    <input
                        type="number"
                        name="max_income"
                        value={formData.max_income}
                        onChange={handleChange}
                        step="0.01"
                        className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                </label>
                <label className="block">
                    <span className="text-gray-700">Rate (% as decimal, e.g., 0.20 for 20%):</span>
                    <input
                        type="number"
                        name="rate"
                        value={formData.rate}
                        onChange={handleChange}
                        step="0.001"
                        required
                        className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                </label>
                <label className="block">
                    <span className="text-gray-700">Deduction:</span>
                    <input
                        type="number"
                        name="deduction"
                        value={formData.deduction}
                        onChange={handleChange}
                        step="0.01"
                        required
                        className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                </label>
                <label className="block">
                    <span className="text-gray-700">Active From:</span>
                    <input
                        type="date"
                        name="active_from"
                        value={formData.active_from}
                        onChange={handleChange}
                        required
                        className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                </label>
                <div className="md:col-span-2 flex justify-end gap-3 mt-4">
                    <button
                        type="submit"
                        className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-md shadow-sm transition duration-200 ease-in-out text-base"
                    >
                        {editingId ? 'Update Bracket' : 'Add Bracket'}
                    </button>
                    {editingId && (
                        <button
                            type="button"
                            onClick={() => {
                                setEditingId(null);
                                setFormData({
                                    currency: 'USD',
                                    min_income: '',
                                    max_income: '',
                                    rate: '',
                                    deduction: '',
                                    active_from: new Date().toISOString().split('T')[0],
                                });
                            }}
                            className="bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-md shadow-sm transition duration-200 ease-in-out text-base"
                        >
                            Cancel Edit
                        </button>
                    )}
                </div>
            </form>

            <h3 className="text-xl font-semibold mb-4 text-gray-700">Existing Tax Brackets</h3>
            <div className="overflow-x-auto">
                <table className="min-w-full bg-white border border-gray-200 rounded-md">
                    <thead>
                        <tr>
                            <th className="py-3 px-4 bg-gray-100 border-b border-gray-200 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                ID
                            </th>
                            <th className="py-3 px-4 bg-gray-100 border-b border-gray-200 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Currency
                            </th>
                            <th className="py-3 px-4 bg-gray-100 border-b border-gray-200 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Min Income
                            </th>
                            <th className="py-3 px-4 bg-gray-100 border-b border-gray-200 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Max Income
                            </th>
                            <th className="py-3 px-4 bg-gray-100 border-b border-gray-200 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Rate
                            </th>
                            <th className="py-3 px-4 bg-gray-100 border-b border-gray-200 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Deduction
                            </th>
                            <th className="py-3 px-4 bg-gray-100 border-b border-gray-200 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Active From
                            </th>
                            <th className="py-3 px-4 bg-gray-100 border-b border-gray-200 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Actions
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {taxBrackets.map((bracket) => (
                            <tr key={bracket.id} className="hover:bg-gray-50">
                                <td className="py-3 px-4 border-b border-gray-200 text-sm">{bracket.id}</td>
                                <td className="py-3 px-4 border-b border-gray-200 text-sm">{bracket.currency}</td>
                                <td className="py-3 px-4 border-b border-gray-200 text-sm">${bracket.min_income}</td>
                                <td className="py-3 px-4 border-b border-gray-200 text-sm">{bracket.max_income ? `$${bracket.max_income}` : 'MAX'}</td>
                                <td className="py-3 px-4 border-b border-gray-200 text-sm">{(bracket.rate * 100).toFixed(1)}%</td>
                                <td className="py-3 px-4 border-b border-gray-200 text-sm">${bracket.deduction}</td>
                                <td className="py-3 px-4 border-b border-gray-200 text-sm">{bracket.active_from}</td>
                                <td className="py-3 px-4 border-b border-gray-200 text-sm whitespace-nowrap">
                                    <button
                                        onClick={() => handleEdit(bracket)}
                                        className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-3 rounded-md shadow-sm transition duration-200 ease-in-out text-sm mr-2"
                                    >
                                        Edit
                                    </button>
                                    <button
                                        onClick={() => handleDelete(bracket.id)}
                                        className="bg-red-600 hover:bg-red-700 text-white py-2 px-3 rounded-md shadow-sm transition duration-200 ease-in-out text-sm"
                                    >
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default TaxConfig;