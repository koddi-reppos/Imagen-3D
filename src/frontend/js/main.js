// Global variables
let scene, camera, renderer;
let selectedFiles = new Set();

// API base URL
const API_BASE = '/api';

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initThreeJS();
    refreshFileList();
    updateParameterForm();
});

// Initialize Three.js for 3D preview
function initThreeJS() {
    const container = document.getElementById('preview3d');
    const containerRect = container.getBoundingClientRect();
    
    // Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0);
    
    // Camera
    camera = new THREE.PerspectiveCamera(75, containerRect.width / containerRect.height, 0.1, 1000);
    camera.position.set(30, 30, 30);
    camera.lookAt(0, 0, 0);
    
    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(containerRect.width, containerRect.height);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    
    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(50, 50, 50);
    directionalLight.castShadow = true;
    scene.add(directionalLight);
    
    // Controls (basic orbit)
    setupBasicControls();
    
    // Clear container and add renderer
    container.innerHTML = '';
    container.appendChild(renderer.domElement);
    
    // Start render loop
    animate();
}

// Basic mouse controls for camera
function setupBasicControls() {
    let isMouseDown = false;
    let mouseX = 0, mouseY = 0;
    
    renderer.domElement.addEventListener('mousedown', (event) => {
        isMouseDown = true;
        mouseX = event.clientX;
        mouseY = event.clientY;
    });
    
    renderer.domElement.addEventListener('mouseup', () => {
        isMouseDown = false;
    });
    
    renderer.domElement.addEventListener('mousemove', (event) => {
        if (!isMouseDown) return;
        
        const deltaX = event.clientX - mouseX;
        const deltaY = event.clientY - mouseY;
        
        // Rotate camera around origin
        const spherical = new THREE.Spherical();
        spherical.setFromVector3(camera.position);
        spherical.theta -= deltaX * 0.01;
        spherical.phi += deltaY * 0.01;
        spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi));
        
        camera.position.setFromSpherical(spherical);
        camera.lookAt(0, 0, 0);
        
        mouseX = event.clientX;
        mouseY = event.clientY;
    });
    
    // Zoom with mouse wheel
    renderer.domElement.addEventListener('wheel', (event) => {
        const distance = camera.position.length();
        const newDistance = distance + event.deltaY * 0.01;
        camera.position.normalize().multiplyScalar(Math.max(5, Math.min(100, newDistance)));
    });
}

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}

// Update parameter form based on selected model type
function updateParameterForm() {
    const modelType = document.getElementById('modelType').value;
    const forms = document.querySelectorAll('.parameter-form');
    
    forms.forEach(form => form.classList.remove('active'));
    document.getElementById(modelType + 'Form').classList.add('active');
    
    // Load templates if AI model is selected
    if (modelType === 'ai_model') {
        loadAITemplates();
    }
}

// Toggle between template and custom AI modes
function toggleAIMode() {
    const mode = document.querySelector('input[name="aiMode"]:checked').value;
    
    if (mode === 'template') {
        document.getElementById('templateMode').style.display = 'block';
        document.getElementById('customMode').style.display = 'none';
    } else {
        document.getElementById('templateMode').style.display = 'none';
        document.getElementById('customMode').style.display = 'block';
    }
}

// Load available AI templates
async function loadAITemplates() {
    try {
        const response = await fetch(`${API_BASE}/templates`);
        const data = await response.json();
        
        if (data.templates) {
            const select = document.getElementById('aiTemplate');
            select.innerHTML = '';
            
            Object.entries(data.templates).forEach(([id, template]) => {
                const option = document.createElement('option');
                option.value = id;
                option.textContent = template.description || id;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading templates:', error);
    }
}

// Get current parameters based on model type
function getCurrentParameters() {
    const modelType = document.getElementById('modelType').value;
    
    switch(modelType) {
        case 'ai_model':
            const aiMode = document.querySelector('input[name="aiMode"]:checked').value;
            if (aiMode === 'template') {
                return {
                    template_id: document.getElementById('aiTemplate').value,
                    style: 'realistic'
                };
            } else {
                return {
                    custom_prompt: document.getElementById('customPrompt').value,
                    style: document.getElementById('aiStyle').value
                };
            }
        case 'cube':
            return {
                size: parseFloat(document.getElementById('cubeSize').value)
            };
        case 'cylinder':
            return {
                radius: parseFloat(document.getElementById('cylinderRadius').value),
                height: parseFloat(document.getElementById('cylinderHeight').value),
                segments: parseInt(document.getElementById('cylinderSegments').value)
            };
        case 'sphere':
            return {
                radius: parseFloat(document.getElementById('sphereRadius').value),
                segments: parseInt(document.getElementById('sphereSegments').value)
            };
        case 'custom_box':
            return {
                length: parseFloat(document.getElementById('boxLength').value),
                width: parseFloat(document.getElementById('boxWidth').value),
                height: parseFloat(document.getElementById('boxHeight').value),
                wall_thickness: parseFloat(document.getElementById('boxThickness').value)
            };
        default:
            return {};
    }
}

// Show status message
function showStatus(message, type = 'success') {
    const statusDiv = document.getElementById('statusMessage');
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${type}`;
    
    if (type === 'success') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
}

// Generate 3D model
async function generateModel() {
    const modelType = document.getElementById('modelType').value;
    const params = getCurrentParameters();
    
    // Validate AI model inputs
    if (modelType === 'ai_model') {
        const aiMode = document.querySelector('input[name="aiMode"]:checked').value;
        
        if (aiMode === 'template' && !params.template_id) {
            showStatus('❌ Selecciona una plantilla', 'error');
            return;
        }
        
        if (aiMode === 'custom' && !params.custom_prompt?.trim()) {
            showStatus('❌ Describe tu modelo en el campo de texto', 'error');
            return;
        }
        
        if (modelType === 'ai_model') {
            showStatus('🤖 Generando modelo AI profesional... Esto puede tomar 2-5 minutos', 'loading');
        }
    } else {
        showStatus('Generando modelo...', 'loading');
    }
    
    try {
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model_type: modelType,
                params: params
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            const metadata = result.metadata;
            let message = `✅ Modelo generado: ${metadata.filename}`;
            
            if (metadata.category) {
                message += ` (${metadata.category})`;
            }
            if (metadata.ai_provider === 'meshy') {
                message += ' - ⭐ Calidad profesional AI';
            }
            
            showStatus(message, 'success');
            await refreshFileList();
            
            // Show model info
            updateModelInfo(metadata);
        } else {
            showStatus(`❌ Error: ${result.message}`, 'error');
        }
    } catch (error) {
        showStatus(`❌ Error de conexión: ${error.message}`, 'error');
    }
}

// Preview model in 3D
function previewModel() {
    const modelType = document.getElementById('modelType').value;
    const params = getCurrentParameters();
    
    // Clear previous model
    scene.children = scene.children.filter(child => 
        child.type === 'AmbientLight' || child.type === 'DirectionalLight'
    );
    
    // Create preview geometry
    let geometry;
    const material = new THREE.MeshLambertMaterial({ 
        color: 0x4299e1,
        transparent: true,
        opacity: 0.8
    });
    
    switch(modelType) {
        case 'cube':
            geometry = new THREE.BoxGeometry(params.size, params.size, params.size);
            break;
        case 'cylinder':
            geometry = new THREE.CylinderGeometry(params.radius, params.radius, params.height, params.segments);
            break;
        case 'sphere':
            geometry = new THREE.SphereGeometry(params.radius, params.segments, params.segments / 2);
            break;
        case 'custom_box':
            // Create a simple box for preview (simplified)
            geometry = new THREE.BoxGeometry(params.length, params.height, params.width);
            break;
    }
    
    if (geometry) {
        const mesh = new THREE.Mesh(geometry, material);
        
        // Position cube at origin, others centered
        if (modelType === 'cube' || modelType === 'custom_box') {
            mesh.position.set(params.size ? params.size/2 : params.length/2, 
                            params.size ? params.size/2 : params.height/2, 
                            params.size ? params.size/2 : params.width/2);
        }
        
        scene.add(mesh);
        
        // Add wireframe
        const wireframe = new THREE.WireframeGeometry(geometry);
        const line = new THREE.LineSegments(wireframe, new THREE.LineBasicMaterial({ color: 0x000000, opacity: 0.3 }));
        line.position.copy(mesh.position);
        scene.add(line);
        
        showStatus('👁️ Vista previa actualizada', 'success');
    }
}

// Update model info display
function updateModelInfo(metadata) {
    const infoDiv = document.getElementById('modelInfo');
    
    let info = `
        <strong>Archivo:</strong> ${metadata.filename}<br>
        <strong>Tipo:</strong> ${metadata.model_type}<br>
    `;
    
    if (metadata.category) {
        info += `<strong>Categoría:</strong> ${metadata.category}<br>`;
    }
    
    if (metadata.prompt) {
        info += `<strong>Descripción:</strong> ${metadata.prompt}<br>`;
    }
    
    if (metadata.ai_provider) {
        info += `<strong>Generado con:</strong> ${metadata.ai_provider} AI<br>`;
    }
    
    info += `
        <strong>Triángulos:</strong> ${metadata.triangles}<br>
        <strong>Tamaño:</strong> ${formatFileSize(metadata.size_bytes)}<br>
        <strong>Creado:</strong> ${new Date(metadata.created_at).toLocaleString()}
    `;
    
    infoDiv.innerHTML = info;
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Refresh file list
async function refreshFileList() {
    try {
        const response = await fetch(`${API_BASE}/files`);
        const data = await response.json();
        
        const filesDiv = document.getElementById('filesList');
        
        if (data.files.length === 0) {
            filesDiv.innerHTML = '<p>No hay archivos generados aún.</p>';
            return;
        }
        
        let html = '';
        data.files.forEach(file => {
            html += `
                <div class="file-item">
                    <div class="file-actions">
                        <input type="checkbox" class="file-checkbox" data-filename="${file.filename}" 
                               onchange="toggleFileSelection('${file.filename}')">
                    </div>
                    <div class="file-info">
                        <div class="file-name">${file.filename}</div>
                        <div class="file-details">
                            ${file.model_type} • ${file.triangles} triángulos • ${formatFileSize(file.size_bytes)} • 
                            ${new Date(file.created_at).toLocaleDateString()}
                        </div>
                    </div>
                    <div class="file-actions">
                        <a href="${API_BASE}/files/${file.filename}" class="download-link" download>
                            📥 Descargar
                        </a>
                    </div>
                </div>
            `;
        });
        
        filesDiv.innerHTML = html;
        updateZipButton();
    } catch (error) {
        document.getElementById('filesList').innerHTML = `<p>Error al cargar archivos: ${error.message}</p>`;
    }
}

// Toggle file selection
function toggleFileSelection(filename) {
    if (selectedFiles.has(filename)) {
        selectedFiles.delete(filename);
    } else {
        selectedFiles.add(filename);
    }
    updateZipButton();
}

// Update ZIP button state
function updateZipButton() {
    const zipBtn = document.getElementById('zipBtn');
    zipBtn.disabled = selectedFiles.size === 0;
    zipBtn.textContent = `📦 Descargar ZIP (${selectedFiles.size})`;
}

// Download selected files as ZIP
async function downloadSelectedAsZip() {
    if (selectedFiles.size === 0) return;
    
    try {
        const response = await fetch(`${API_BASE}/zip`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filenames: Array.from(selectedFiles)
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `modelos_3d_${new Date().toISOString().slice(0,10)}.zip`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showStatus(`✅ ZIP descargado con ${selectedFiles.size} archivos`, 'success');
            
            // Clear selection
            selectedFiles.clear();
            document.querySelectorAll('.file-checkbox').forEach(cb => cb.checked = false);
            updateZipButton();
        } else {
            showStatus('❌ Error al crear ZIP', 'error');
        }
    } catch (error) {
        showStatus(`❌ Error: ${error.message}`, 'error');
    }
}