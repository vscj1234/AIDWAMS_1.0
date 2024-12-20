// Add this at the start of your JavaScript file
console.log('Script loaded');

// Load approvers when page loads
async function loadApprovers() {
    console.log('Loading approvers...');
    const select = document.getElementById('approverSelect');
    
    try {
        // Show loading state
        select.innerHTML = '<option value="">Loading approvers...</option>';
        
        const response = await fetch('/approvers/');
        console.log('Response status:', response.status);
        
        const data = await response.json();
        console.log('Received data:', data);
        
        // Clear and add default option
        select.innerHTML = '<option value="">Select Approver</option>';
        
        if (data.approvers && Array.isArray(data.approvers)) {
            if (data.approvers.length === 0) {
                console.log('No approvers found in the data');
                select.innerHTML = '<option value="">No approvers available</option>';
            } else {
                data.approvers.forEach(approver => {
                    console.log('Adding approver:', approver);
                    const option = document.createElement('option');
                    option.value = approver;
                    option.textContent = approver;
                    select.appendChild(option);
                });
            }
        } else {
            console.error('Invalid approvers data received:', data);
            select.innerHTML = '<option value="">Error loading approvers</option>';
        }
    } catch (error) {
        console.error('Failed to load approvers:', error);
        select.innerHTML = '<option value="">Error loading approvers</option>';
    }
}

// Call loadApprovers when page loads
document.addEventListener('DOMContentLoaded', loadApprovers);

async function uploadInvoice() {
    const fileInput = document.getElementById('invoiceUpload');
    const approverSelect = document.getElementById('approverSelect');
    const resultDiv = document.getElementById('result');
    
    if (!fileInput.files.length) {
        resultDiv.innerHTML = '<p class="error">Please select a file</p>';
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('approver', approverSelect.value);
    
    // Show loading state
    resultDiv.innerHTML = `
        <p><span class="processing-spinner"></span>Processing document...</p>
        <p class="file-info">
            File: ${fileInput.files[0].name}<br>
            Size: ${(fileInput.files[0].size / (1024 * 1024)).toFixed(2)} MB
        </p>
    `;
    
    try {
        const response = await fetch('/upload-invoice/', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            resultDiv.innerHTML = `
                <div class="success-result">
                    <h2>Document Analysis:</h2>
                    <p class="doc-type">Type: ${result.document_type.document_type} 
                        (Confidence: ${(result.document_type.confidence * 100).toFixed(1)}%)</p>
                    <p class="doc-reasoning">Reasoning: ${result.document_type.reasoning}</p>
                    <h2>Extracted Information:</h2>
                    <p class="key-points">${result.key_points}</p>
                    ${result.email_sent ? 
                        `<p class="email-status success">✓ Email sent successfully to ${result.approver}</p>` :
                        '<p class="email-status warning">⚠ No email sent</p>'
                    }
                    <details>
                        <summary>Show Full Extracted Text</summary>
                        <pre>${result.extracted_text}</pre>
                    </details>
                </div>
            `;
        } else {
            resultDiv.innerHTML = `<p class="error">Error: ${result.message}</p>`;
        }
    } catch (error) {
        console.error('Upload failed:', error);
        resultDiv.innerHTML = `<p class="error">Upload failed: ${error.message}</p>`;
    }
}