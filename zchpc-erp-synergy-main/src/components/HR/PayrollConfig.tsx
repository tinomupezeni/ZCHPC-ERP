// src/components/PayrollConfig.js
import React, { useState, useEffect } from 'react';
import { getPayrollPeriods, createPayrollPeriod, updatePayrollPeriod, deletePayrollPeriod } from '../../server/api';

const PayrollConfig = () => {
    const [payrollPeriods, setPayrollPeriods] = useState([]);
    const [formData, setFormData] = useState({
        name: '',
        frequency_in_days: '',
    });
    const [editingId, setEditingId] = useState(null);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        fetchPayrollPeriods();
    }, []);

    const fetchPayrollPeriods = async () => {
        try {
            const response = await getPayrollPeriods();
            console.log(response);
            
            setPayrollPeriods(response.data.sort((a, b) => a.name.localeCompare(b.name)));
            setError('');
        } catch (err) {
            setError('Failed to fetch payroll periods.');
            console.error('Error fetching payroll periods:', err);
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
                frequency_in_days: parseInt(formData.frequency_in_days),
            };

            if (editingId) {
                await updatePayrollPeriod(editingId, dataToSubmit);
                setMessage('Payroll period updated successfully!');
            } else {
                await createPayrollPeriod(dataToSubmit);
                setMessage('Payroll period created successfully!');
                setFormData({ name: '', frequency_in_days: '' }); // Reset form
            }
            setEditingId(null); // Exit edit mode
            fetchPayrollPeriods(); // Refresh list
        } catch (err) {
            setError(`Failed to save payroll period: ${err.response?.data ? JSON.stringify(err.response.data) : err.message}`);
            console.error('Error saving payroll period:', err);
        }
    };

    const handleEdit = (period) => {
        setFormData({
            name: period.name,
            frequency_in_days: period.frequency_in_days,
        });
        setEditingId(period.id);
        setMessage('');
        setError('');
    };

    const handleDelete = async (id) => {
        if (window.confirm('Are you sure you want to delete this payroll period type?')) {
            setMessage('');
            setError('');
            try {
                await deletePayrollPeriod(id);
                setMessage('Payroll period type deleted successfully!');
                fetchPayrollPeriods();
            } catch (err) {
                setError('Failed to delete payroll period type.');
                console.error('Error deleting payroll period type:', err);
            }
        }
    };

    return (
        <div className="font-sans p-5 max-w-4xl mx-auto my-5 border border-gray-300 rounded-lg shadow-md bg-gray-50">
            <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Manage Payroll Period Types</h2>
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
                    <span className="text-gray-700">Period Name:</span>
                    <input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        required
                        className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        placeholder="e.g., Monthly"
                    />
                </label>
                <label className="block">
                    <span className="text-gray-700">Frequency in Days (approximate):</span>
                    <input
                        type="number"
                        name="frequency_in_days"
                        value={formData.frequency_in_days}
                        onChange={handleChange}
                        required
                        className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        placeholder="e.g., 30 for monthly, 14 for bi-weekly"
                    />
                </label>

                <div className="md:col-span-2 flex justify-end gap-3 mt-4">
                    <button
                        type="submit"
                        className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-md shadow-sm transition duration-200 ease-in-out text-base"
                    >
                        {editingId ? 'Update Period' : 'Add Period'}
                    </button>
                    {editingId && (
                        <button
                            type="button"
                            onClick={() => {
                                setEditingId(null);
                                setFormData({ name: '', frequency_in_days: '' });
                            }}
                            className="bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-md shadow-sm transition duration-200 ease-in-out text-base"
                        >
                            Cancel Edit
                        </button>
                    )}
                </div>
            </form>

            <h3 className="text-xl font-semibold mb-4 text-gray-700">Existing Payroll Period Types</h3>
            <div className="overflow-x-auto">
                <table className="min-w-full bg-white border border-gray-200 rounded-md">
                    <thead>
                        <tr>
                            <th className="py-3 px-4 bg-gray-100 border-b border-gray-200 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                ID
                            </th>
                            <th className="py-3 px-4 bg-gray-100 border-b border-gray-200 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Name
                            </th>
                            <th className="py-3 px-4 bg-gray-100 border-b border-gray-200 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Frequency (Days)
                            </th>
                            <th className="py-3 px-4 bg-gray-100 border-b border-gray-200 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                                Actions
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {payrollPeriods.map((period) => (
                            <tr key={period.id} className="hover:bg-gray-50">
                                <td className="py-3 px-4 border-b border-gray-200 text-sm">{period.id}</td>
                                <td className="py-3 px-4 border-b border-gray-200 text-sm">{period.name}</td>
                                <td className="py-3 px-4 border-b border-gray-200 text-sm">{period.frequency_in_days}</td>
                                <td className="py-3 px-4 border-b border-gray-200 text-sm whitespace-nowrap">
                                    <button
                                        onClick={() => handleEdit(period)}
                                        className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-3 rounded-md shadow-sm transition duration-200 ease-in-out text-sm mr-2"
                                    >
                                        Edit
                                    </button>
                                    <button
                                        onClick={() => handleDelete(period.id)}
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

export default PayrollConfig;