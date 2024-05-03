import React, { useState } from 'react';
import axios from 'axios';
import './App.css'; // Import CSS file for styling

const App = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [downloadLink, setDownloadLink] = useState(null);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setDownloadLink(null);
  
    const formData = new FormData();
    formData.append('file', file);
  
    try {
      const response = await axios.post('http://localhost:8000/predict', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        responseType: 'arraybuffer', // Ensure binary response
      });
  
      if (response && response.data) {
        // Create Blob from binary data
        const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        const downloadUrl = URL.createObjectURL(blob);
        setDownloadLink(downloadUrl);
      } else {
        setError('An error occurred while processing the request.');
      }
    } catch (error) {
      if (error.response && error.response.data && error.response.data.error) {
        setError(error.response.data.error);
      } else {
        setError('An error occurred while processing the request.');
      }
    }
  
    setLoading(false);
  };

  return (
    <div className="container">
      <h1 className="title">Exoplanet Prediction App</h1>
      <f1 className="title">Powered by Spartificial</f1>
      <div className="footer"> Designed and Developed by Ahamika Pattnaik, Durgesh Duklan, Sukant Neve, Zainul Panjwani </div>
      <form onSubmit={handleSubmit} className="form">
        <input type="file" onChange={handleFileChange} className="file-input" />
        <button type="submit" disabled={!file || loading} className="submit-btn">
          {loading ? 'Loading...' : 'Upload'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {downloadLink && (
        <div className="download-section">
          <h2 className="download-title">Download Predictions</h2>
          <a href={downloadLink} download="predictions.xlsx" className="download-link">
            Download Predictions
          </a>
        </div>
      )}
    </div>
  
  );

};

export default App;
