function copyToClipboard(networkKey) {
    // Find the row for this network
    const rows = document.querySelectorAll('tr');
    let targetRow = null;
    
    for (let row of rows) {
        const networkKeyCell = row.querySelector('.field-network_key');
        if (networkKeyCell && networkKeyCell.textContent.trim() === networkKey) {
            targetRow = row;
            break;
        }
    }
    
    if (!targetRow) {
        alert('Could not find network row');
        return;
    }
    
    // Find the postback URL cell
    const urlCell = targetRow.querySelector('.field-get_postback_url_display');
    if (!urlCell) {
        alert('Could not find postback URL cell');
        return;
    }
    
    // Find the URL text (first div with monospace font)
    const urlDiv = urlCell.querySelector('div:first-child');
    if (!urlDiv) {
        alert('Could not find postback URL text');
        return;
    }
    
    const urlText = urlDiv.textContent.trim();
    if (!urlText) {
        alert('Postback URL is empty');
        return;
    }
    
    // Copy the URL to clipboard
    copyTextToClipboard(urlText);
    showCopySuccess(networkKey);
}

function copyTextToClipboard(text) {
    // Create a temporary textarea element
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    
    // Select and copy the text
    textarea.select();
    textarea.setSelectionRange(0, 99999); // For mobile devices
    
    try {
        document.execCommand('copy');
        console.log('URL copied to clipboard:', text);
    } catch (err) {
        console.error('Failed to copy text: ', err);
        alert('Failed to copy URL. Please copy manually.');
    }
    
    // Remove the temporary element
    document.body.removeChild(textarea);
}

function showCopySuccess(networkKey) {
    // Find the copy button and update its text
    const button = document.querySelector(`button[onclick="copyToClipboard('${networkKey}')"]`);
    if (button) {
        const originalText = button.textContent;
        const originalBackground = button.style.background;
        
        button.textContent = 'Copied!';
        button.style.background = '#28a745';
        
        // Reset after 2 seconds
        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = originalBackground;
        }, 2000);
    }
}

// Add click event listeners when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Copy postback URL script loaded');
    
    // Add data attributes to table rows for easier selection
    const rows = document.querySelectorAll('tr');
    rows.forEach(row => {
        const networkKeyCell = row.querySelector('.field-network_key');
        if (networkKeyCell) {
            const networkKey = networkKeyCell.textContent.trim();
            row.setAttribute('data-network', networkKey);
        }
    });
}); 