/* ============================================
   3D INTERACTIVE CYBER BACKGROUND
   By Om Kumar - CyberDefender OM
   ============================================ */

// =============================================
// 1. THREE.JS 3D HOLOGRAPHIC THREAT GLOBE
// =============================================
(function() {
    const container = document.getElementById('globeCanvas');
    if (!container || typeof THREE === 'undefined') return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 1000);
    camera.position.z = 5.5;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    const initSize = Math.min(window.innerWidth * 0.7, 700);
    renderer.setSize(initSize, initSize);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    const globeGroup = new THREE.Group();
    scene.add(globeGroup);

    // Wireframe globe
    const globeGeo = new THREE.SphereGeometry(2, 32, 32);
    const globeMat = new THREE.MeshBasicMaterial({
        color: 0x00ff9d,
        wireframe: true,
        transparent: true,
        opacity: 0.22
    });
    globeGroup.add(new THREE.Mesh(globeGeo, globeMat));

    // Inner glow sphere
    const glowGeo = new THREE.SphereGeometry(1.97, 32, 32);
    const glowMat = new THREE.MeshBasicMaterial({
        color: 0x00f0ff,
        transparent: true,
        opacity: 0.07
    });
    globeGroup.add(new THREE.Mesh(glowGeo, glowMat));

    // Outer glow halo
    const haloGeo = new THREE.SphereGeometry(2.2, 32, 32);
    const haloMat = new THREE.MeshBasicMaterial({
        color: 0x00ff9d,
        transparent: true,
        opacity: 0.03,
        side: THREE.BackSide
    });
    globeGroup.add(new THREE.Mesh(haloGeo, haloMat));

    // Orbiting rings
    const ring1 = new THREE.Mesh(
        new THREE.TorusGeometry(2.5, 0.008, 8, 100),
        new THREE.MeshBasicMaterial({ color: 0x00ff9d, transparent: true, opacity: 0.5 })
    );
    ring1.rotation.x = Math.PI / 3;
    globeGroup.add(ring1);

    const ring2 = new THREE.Mesh(
        new THREE.TorusGeometry(2.8, 0.008, 8, 100),
        new THREE.MeshBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.4 })
    );
    ring2.rotation.x = -Math.PI / 4;
    ring2.rotation.y = Math.PI / 6;
    globeGroup.add(ring2);

    const ring3 = new THREE.Mesh(
        new THREE.TorusGeometry(3.1, 0.005, 8, 100),
        new THREE.MeshBasicMaterial({ color: 0xa050ff, transparent: true, opacity: 0.3 })
    );
    ring3.rotation.x = Math.PI / 2;
    ring3.rotation.z = Math.PI / 5;
    globeGroup.add(ring3);

    // Threat nodes on globe
    const nodePositions = [];
    const nodeCount = 45;
    for (let i = 0; i < nodeCount; i++) {
        const phi = Math.acos(-1 + (2 * i) / nodeCount);
        const theta = Math.sqrt(nodeCount * Math.PI) * phi;
        const r = 2;
        const x = r * Math.cos(theta) * Math.sin(phi);
        const y = r * Math.sin(theta) * Math.sin(phi);
        const z = r * Math.cos(phi);
        nodePositions.push({ x, y, z });

        const nodeGeo = new THREE.SphereGeometry(0.032, 6, 6);
        let color = 0x00ff9d;
        if (i % 5 === 0) color = 0xff0040;       // red threat
        else if (i % 3 === 0) color = 0x00f0ff;  // cyan
        const nodeMat = new THREE.MeshBasicMaterial({ color: color });
        const node = new THREE.Mesh(nodeGeo, nodeMat);
        node.position.set(x, y, z);
        node.userData.pulse = Math.random() * Math.PI * 2;
        globeGroup.add(node);
    }

    // Threat arcs connecting random nodes
    const arcs = [];
    for (let i = 0; i < 15; i++) {
        const a = nodePositions[Math.floor(Math.random() * nodePositions.length)];
        const b = nodePositions[Math.floor(Math.random() * nodePositions.length)];
        if (a === b) continue;

        const points = [];
        const segments = 40;
        for (let j = 0; j <= segments; j++) {
            const t = j / segments;
            const x = a.x * (1 - t) + b.x * t;
            const y = a.y * (1 - t) + b.y * t;
            const z = a.z * (1 - t) + b.z * t;
            const len = Math.sqrt(x * x + y * y + z * z) || 1;
            const arcHeight = 1 + Math.sin(Math.PI * t) * 0.35;
            points.push(new THREE.Vector3(
                (x / len) * arcHeight * 2,
                (y / len) * arcHeight * 2,
                (z / len) * arcHeight * 2
            ));
        }

        const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
        const isThreat = Math.random() > 0.7;
        const lineMat = new THREE.LineBasicMaterial({
            color: isThreat ? 0xff0040 : (Math.random() > 0.5 ? 0x00ff9d : 0x00f0ff),
            transparent: true,
            opacity: isThreat ? 0.7 : 0.5
        });
        const line = new THREE.Line(lineGeo, lineMat);
        line.userData.phase = Math.random() * Math.PI * 2;
        globeGroup.add(line);
        arcs.push(line);
    }

    // Mouse interaction
    let targetRotX = 0, targetRotY = 0;
    let currentRotX = 0, currentRotY = 0;

    document.addEventListener('mousemove', (e) => {
        targetRotY = ((e.clientX / window.innerWidth) * 2 - 1) * 0.6;
        targetRotX = -((e.clientY / window.innerHeight) * 2 - 1) * 0.35;
    });

    document.addEventListener('touchmove', (e) => {
        if (!e.touches[0]) return;
        targetRotY = ((e.touches[0].clientX / window.innerWidth) * 2 - 1) * 0.6;
        targetRotX = -((e.touches[0].clientY / window.innerHeight) * 2 - 1) * 0.35;
    }, { passive: true });

    // Animation
    let time = 0;
    function animate() {
        requestAnimationFrame(animate);
        time += 0.016;

        globeGroup.rotation.y += 0.0025;
        ring1.rotation.z += 0.003;
        ring2.rotation.z -= 0.002;
        ring3.rotation.y += 0.004;

        // Smooth camera tilt from mouse
        currentRotX += (targetRotX - currentRotX) * 0.05;
        currentRotY += (targetRotY - currentRotY) * 0.05;
        camera.position.x = currentRotY * 1.5;
        camera.position.y = currentRotX * 1.5;
        camera.lookAt(0, 0, 0);

        // Pulse nodes
        globeGroup.children.forEach((child) => {
            if (child.userData.pulse !== undefined) {
                child.userData.pulse += 0.05;
                const s = 1 + Math.sin(child.userData.pulse) * 0.5;
                child.scale.set(s, s, s);
            }
        });

        // Arc glow animation
        arcs.forEach((arc) => {
            arc.userData.phase += 0.03;
            arc.material.opacity = 0.3 + Math.sin(arc.userData.phase) * 0.4;
        });

        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        const newSize = Math.min(window.innerWidth * 0.7, 700);
        renderer.setSize(newSize, newSize);
    });
})();


// =============================================
// 2. INTERACTIVE PARTICLE NODE MESH
// =============================================
(function() {
    const canvas = document.getElementById('particleCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let w, h;
    function resize() {
        w = canvas.width = window.innerWidth;
        h = canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    const particles = [];
    const PARTICLE_COUNT = window.innerWidth < 768 ? 35 : 80;
    const CONNECTION_DIST = window.innerWidth < 768 ? 90 : 130;

    let mouseX = -1000, mouseY = -1000;
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });
    document.addEventListener('mouseleave', () => {
        mouseX = -1000;
        mouseY = -1000;
    });

    for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push({
            x: Math.random() * w,
            y: Math.random() * h,
            vx: (Math.random() - 0.5) * 0.4,
            vy: (Math.random() - 0.5) * 0.4,
            size: Math.random() * 1.8 + 0.6,
            color: Math.random() > 0.5 ? '0,255,157' : '0,240,255'
        });
    }

    function draw() {
        ctx.clearRect(0, 0, w, h);

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];

            const dx = p.x - mouseX;
            const dy = p.y - mouseY;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 160 && dist > 0) {
                const force = (160 - dist) / 160;
                p.vx += (dx / dist) * force * 0.4;
                p.vy += (dy / dist) * force * 0.4;
            }

            p.x += p.vx;
            p.y += p.vy;

            const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
            if (speed > 1.5) {
                p.vx = (p.vx / speed) * 1.5;
                p.vy = (p.vy / speed) * 1.5;
            }

            p.vx *= 0.985;
            p.vy *= 0.985;

            if (p.x < 0 || p.x > w) p.vx *= -1;
            if (p.y < 0 || p.y > h) p.vy *= -1;
            p.x = Math.max(0, Math.min(w, p.x));
            p.y = Math.max(0, Math.min(h, p.y));

            // Draw connections
            for (let j = i + 1; j < particles.length; j++) {
                const p2 = particles[j];
                const ddx = p.x - p2.x;
                const ddy = p.y - p2.y;
                const d = Math.sqrt(ddx * ddx + ddy * ddy);
                if (d < CONNECTION_DIST) {
                    const alpha = (1 - d / CONNECTION_DIST) * 0.25;
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.strokeStyle = 'rgba(0,255,157,' + alpha + ')';
                    ctx.lineWidth = 0.6;
                    ctx.stroke();
                }
            }

            // Draw particle
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(' + p.color + ',0.85)';
            ctx.shadowBlur = 8;
            ctx.shadowColor = 'rgba(' + p.color + ',0.9)';
            ctx.fill();
            ctx.shadowBlur = 0;
        }

        requestAnimationFrame(draw);
    }
    draw();
})();


// =============================================
// 3. MATRIX RAIN EFFECT
// =============================================
(function() {
    const canvas = document.getElementById('matrixCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let w, h;
    function resize() {
        w = canvas.width = window.innerWidth;
        h = canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    const chars = '01アイウエオカキクケコサシスセソタチツテトナニヌネノ';
    const fontSize = 14;
    let columns = Math.floor(w / fontSize);
    let drops = Array(columns).fill(1);

    window.addEventListener('resize', () => {
        columns = Math.floor(w / fontSize);
        drops = Array(columns).fill(1);
    });

    function draw() {
        ctx.fillStyle = 'rgba(2, 13, 24, 0.08)';
        ctx.fillRect(0, 0, w, h);
        ctx.fillStyle = 'rgba(0, 255, 157, 0.6)';
        ctx.font = fontSize + 'px monospace';

        for (let i = 0; i < drops.length; i++) {
            const text = chars[Math.floor(Math.random() * chars.length)];
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);
            if (drops[i] * fontSize > h && Math.random() > 0.975) {
                drops[i] = 0;
            }
            drops[i]++;
        }
    }
    setInterval(draw, 60);
})();

console.log('%c🛡️ CyberDefender OM | 3D Cyber Background Loaded', 'color:#00ff9d;font-size:16px;font-weight:bold;');
