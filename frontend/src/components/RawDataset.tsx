import React, { useState, useEffect } from 'react';
import { UploadCloud, FileSpreadsheet, AlertCircle } from 'lucide-react';
import { uploadDataset, getDatasets } from '../api';

const RawDataset = () => {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      const data = await getDatasets();
      setDatasets(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      setError('Only CSV files are supported.');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      await uploadDataset(file);
      await fetchDatasets();
    } catch (err) {
      setError('Failed to upload dataset. Ensure backend is running.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Upload Section */}
      <div className="bg-white p-8 rounded-xl border-2 border-dashed border-gray-300 flex flex-col items-center justify-center text-center hover:bg-gray-50 transition-colors">
        <UploadCloud className="w-12 h-12 text-blue-500 mb-4" />
        <h2 className="text-xl font-semibold mb-2">Upload Raw Dataset</h2>
        <p className="text-gray-500 mb-6">Supported formats: CSV</p>
        
        <label className="cursor-pointer bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors">
          {uploading ? 'Uploading...' : 'Browse CSV'}
          <input 
            type="file" 
            className="hidden" 
            accept=".csv"
            onChange={handleFileUpload}
            disabled={uploading}
          />
        </label>
        {error && <p className="text-red-500 mt-4 flex items-center gap-2"><AlertCircle className="w-4 h-4"/> {error}</p>}
      </div>

      {/* Datasets List */}
      <div className="bg-white rounded-xl border shadow-sm">
        <div className="p-6 border-b">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-gray-500" />
            Uploaded Datasets
          </h3>
        </div>
        <div className="p-0">
          {datasets.length === 0 ? (
            <div className="p-12 text-center text-gray-500">
              Zero datasets found. Upload one to begin.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-gray-50 text-gray-600 text-sm">
                    <th className="p-4 border-b font-medium">Filename</th>
                    <th className="p-4 border-b font-medium">Rows</th>
                    <th className="p-4 border-b font-medium">Time Span</th>
                    <th className="p-4 border-b font-medium">Sensors Detected</th>
                    <th className="p-4 border-b font-medium">Quality Score</th>
                  </tr>
                </thead>
                <tbody>
                  {datasets.map((ds, idx) => (
                    <tr key={idx} className="hover:bg-gray-50 border-b last:border-b-0">
                      <td className="p-4 text-sm font-medium">{ds.filename}</td>
                      <td className="p-4 text-sm text-gray-600">{ds.total_rows.toLocaleString()}</td>
                      <td className="p-4 text-sm text-gray-600">{ds.time_span}</td>
                      <td className="p-4 text-sm text-gray-600">
                         <div className="flex flex-wrap gap-1">
                            {ds.detected_sensors.map((s: string) => (
                               <span key={s} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">{s}</span>
                            ))}
                         </div>
                      </td>
                      <td className="p-4 text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${ds.data_quality_score > 80 ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                           {ds.data_quality_score}/100
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RawDataset;
