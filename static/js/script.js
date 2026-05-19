// static/js/script.js
// Global variables
let currentFileId = null;

// Document ready function
$(document).ready(function () {
    initializeEventHandlers();
});

// Initialize all event handlers
function initializeEventHandlers() {
    const fileInput = $('#fileInput');
    const dropZone = $('#dropZone');
    const analyzeBtn = $('#analyzeBtn');
    const cancelBtn = $('#cancelBtn');
    const downloadReportBtn = $('#downloadReportBtn');
    const newAnalysisBtn = $('#newAnalysisBtn');

    // File input change handler
    fileInput.on('change', function (e) {
        const file = e.target.files[0];
        if (file) {
            uploadFile(file);
        }
    });

    // Drag and drop handlers
    dropZone.on('dragover', function (e) {
        e.preventDefault();
        dropZone.addClass('dragover');
    });

    dropZone.on('dragleave', function () {
        dropZone.removeClass('dragover');
    });

    dropZone.on('drop', function (e) {
        e.preventDefault();
        dropZone.removeClass('dragover');

        const file = e.originalEvent.dataTransfer.files[0];
        if (file) {
            uploadFile(file);
        }
    });

    // Analyze button handler
    analyzeBtn.on('click', function () {
        analyzeImage();
    });

    // Cancel button handler
    cancelBtn.on('click', function () {
        resetUploadForm();
    });

    // Download report button handler
    downloadReportBtn.on('click', function () {
        downloadReport();
    });

    // New analysis button handler
    newAnalysisBtn.on('click', function () {
        resetAnalysis();
    });
}

// Upload file to server
function uploadFile(file) {
    // Check file size
    if (file.size > 10 * 1024 * 1024) {
        alert('File is too large. Maximum size is 10MB');
        return;
    }

    // Check file type
    const fileExtension = file.name.split('.').pop().toLowerCase();
    const allowedExtensions = ['jpg', 'jpeg', 'png', 'dcm'];
    if (!allowedExtensions.includes(fileExtension)) {
        alert('Please upload an image file only (JPEG, PNG, DICOM)');
        return;
    }

    // Show loading indicator
    showLoading('Uploading image...');

    // Create form data
    const formData = new FormData();
    formData.append('file', file);

    // Send AJAX request
    $.ajax({
        url: '/api/upload',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function (response) {
            if (response.success) {
                handleUploadSuccess(response, fileExtension);
            } else {
                handleUploadError(response.error);
            }
        },
        error: function (xhr, status, error) {
            handleUploadError(xhr, error);
        }
    });
}

// Handle successful upload
function handleUploadSuccess(response, fileExtension) {
    // Store file ID
    currentFileId = response.file_id;

    // Display file info
    $('#fileName').text(response.filename);
    $('#fileSize').text(formatFileSize(response.file_size));
    $('#fileType').text(fileExtension.toUpperCase());
    $('#uploadTime').text(new Date().toLocaleString());

    // Display preview image
    $('#previewImage').attr('src', response.image_data);

    // Show preview container
    $('#previewContainer').slideDown();

    // Hide loading indicator
    hideLoading();
}

// Handle upload error
function handleUploadError(xhr, error) {
    hideLoading();
    let errorMsg = 'Upload failed: ';
    if (xhr.responseJSON && xhr.responseJSON.error) {
        errorMsg += xhr.responseJSON.error;
    } else {
        errorMsg += error;
    }
    alert(errorMsg);
}

// Analyze uploaded image
function analyzeImage() {
    if (!currentFileId) {
        alert('Please upload an image first');
        return;
    }

    // Show loading indicator
    showLoading('Analyzing image...');
    $('#analyzeBtn').prop('disabled', true);

    // Send analysis request
    $.ajax({
        url: '/api/analyze',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ file_id: currentFileId }),
        success: function (response) {
            if (response.success) {
                // Display results
                displayResults(response.result);

                // Hide loading indicator
                hideLoading();
            } else {
                handleAnalysisError(response.error);
            }
        },
        error: function (xhr, status, error) {
            handleAnalysisError(xhr, error);
        }
    });
}

// Handle analysis error
function handleAnalysisError(xhr, error) {
    hideLoading();
    $('#analyzeBtn').prop('disabled', false);
    let errorMsg = 'Analysis failed: ';
    if (xhr.responseJSON && xhr.responseJSON.error) {
        errorMsg += xhr.responseJSON.error;
    } else {
        errorMsg += error;
    }
    alert(errorMsg);
    console.error("Analysis error details:", xhr, status, error);
}

// Display analysis results
function displayResults(result) {
    // Reset stage result first
    $('#stageResult').hide();

    // Display normal vs TC result
    const normalConfidenceValue = Math.round(result.confidence * 100);
    $('#normalBar').css('width', normalConfidenceValue + '%');
    $('#normalConfidence').text(normalConfidenceValue + '%');

    if (result.normal) {
        $('#normalResult').addClass('normal-result');
        $('#normalVerdict').text('NORMAL').css('color', 'var(--success-color)');

        // Hide stage section completely for normal cases
        $('#stageResult').hide();
    } else {
        $('#normalResult').addClass('abnormal-result');
        $('#normalVerdict').text('TUMORAL CALCINOSIS DETECTED').css('color', 'var(--warning-color)');

        // Display stage result only if TC detected AND stage info exists
        if (result.stage) {
            $('#stageResult').show();
            const stageConfidenceValue = Math.round(result.stage_confidence * 100);
            $('#stageBar').css('width', stageConfidenceValue + '%');
            $('#stageConfidence').text(stageConfidenceValue + '%');
            $('#stageVerdict').text(result.stage.toUpperCase() + ' STAGE').css('color', 'var(--warning-color)');
        }
    }

    // Show result card
    $('#resultCard').slideDown();
}
// Download report
function downloadReport() {
    if (!currentFileId) return;

    showLoading('Generating report...');

    $.ajax({
        url: '/api/report',
        type: 'GET',
        success: function (response) {
            if (response.success) {
                // In a real implementation, this would download a PDF
                // For now, we'll just show an alert with the report data
                hideLoading();
                alert('Report generated successfully! Report ID: ' + response.report.analysis_id);

                // Here you would typically trigger a download
                // downloadPDF(response.report);
            } else {
                hideLoading();
                alert('Report generation failed: ' + response.error);
            }
        },
        error: function (xhr, status, error) {
            hideLoading();
            alert('Report generation failed: ' + (xhr.responseJSON?.error || error));
        }
    });
}

// Reset upload form
function resetUploadForm() {
    $('#fileInput').val('');
    $('#previewContainer').slideUp();
    $('#resultCard').slideUp();
    $('#analyzeBtn').prop('disabled', false);
    currentFileId = null;
}

// Reset analysis
function resetAnalysis() {
    $('#fileInput').val('');
    $('#previewContainer').slideUp();
    $('#resultCard').slideUp();
    $('#normalResult').removeClass('normal-result abnormal-result');
    $('#stageResult').hide(); // Ensure stage section is hidden on reset
    $('#analyzeBtn').prop('disabled', false);
    currentFileId = null;
}

// Show loading indicator
function showLoading(text) {
    $('#loadingText').text(text);
    $('#loadingIndicator').show();
}

// Hide loading indicator
function hideLoading() {
    $('#loadingIndicator').hide();
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Download PDF report (for future implementation)
function downloadPDF(reportData) {
    // This would be implemented using a PDF generation library
    console.log('Generating PDF for:', reportData);
    // In a real implementation, this would create and trigger a PDF download
}