/* === LIVE CYBER ATTACK WORLD MAP === */
(function() {
    const canvas = document.getElementById('worldMapCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let W, H, MAP_OFFSET_X, MAP_OFFSET_Y, MAP_SCALE;

    // === World Map Coordinates (simplified country locations) ===
    const COUNTRIES = {
        'USA':         { x: 0.22, y: 0.38, name: 'United States' },
        'Canada':      { x: 0.20, y: 0.28, name: 'Canada' },
        'Brazil':      { x: 0.32, y: 0.68, name: 'Brazil' },
        'Argentina':   { x: 0.31, y: 0.80, name: 'Argentina' },
        'UK':          { x: 0.47, y: 0.30, name: 'United Kingdom' },
        'France':      { x: 0.49, y: 0.36, name: 'France' },
        'Germany':     { x: 0.51, y: 0.33, name: 'Germany' },
        'Italy':       { x: 0.52, y: 0.39, name: 'Italy' },
        'Spain':       { x: 0.46, y: 0.40, name: 'Spain' },
        'Russia':      { x: 0.62, y: 0.25, name: 'Russia' },
        'China':       { x: 0.75, y: 0.42, name: 'China' },
        'Japan':       { x: 0.85, y: 0.40, name: 'Japan' },
        'India':       { x: 0.70, y: 0.50, name: 'India' },
        'Pakistan':    { x: 0.67, y: 0.48, name: 'Pakistan' },
        'Iran':        { x: 0.63, y: 0.44, name: 'Iran' },
        'UAE':         { x: 0.64, y: 0.50, name: 'UAE' },
        'Saudi':       { x: 0.61, y: 0.50, name: 'Saudi Arabia' },
        'Australia':   { x: 0.86, y: 0.72, name: 'Australia' },
        'South Africa':{ x: 0.54, y: 0.75, name: 'South Africa' },
        'Egypt':       { x: 0.56, y: 0.48, name: 'Egypt' },
        'Nigeria':     { x: 0.49, y: 0.58, name: 'Nigeria' },
        'South Korea': { x: 0.82, y: 0.42, name: 'South Korea' },
        'Singapore':   { x: 0.78, y: 0.60, name: 'Singapore' },
        'Indonesia':   { x: 0.80, y: 0.65, name: 'Indonesia' },
        'Mexico':      { x: 0.18, y: 0.48, name: 'Mexico' },
        'Ukraine':     { x: 0.56, y: 0.32, name: 'Ukraine' },
        'Israel':      { x: 0.58, y: 0.44, name: 'Israel' },
        'Turkey':      { x: 0.58, y: 0.40, name: 'Turkey' },
        'Vietnam':     { x: 0.78, y: 0.53, name: 'Vietnam' },
        'Thailand':    { x: 0.77, y: 0.55, name: 'Thailand' }
    };

    const COUNTRY_KEYS = Object.keys(COUNTRIES);

    // Attack types
    const ATTACK_TYPES = [
        { name: 'SQL Injection',  severity: 'critical' },
        { name: 'DDoS Attack',    severity: 'critical' },
        { name: 'Phishing',       severity: 'warning' },
        { name: 'XSS Attack',     severity: 'warning' },
        { name: 'Ransomware',     severity: 'critical' },
        { name: 'Brute Force',    severity: 'warning' },
        { name: 'Zero-Day',       severity: 'critical' },
        { name: 'Malware',        severity: 'warning' },
        { name: 'Port Scan',      severity: 'safe' },
        { name: 'MITM Attack',    severity: 'critical' },
        { name: 'Botnet Traffic', severity: 'warning' },
        { name: 'Credential Stuffing', severity: 'warning' }
    ];

    // Map dotted grid generation
    function generateDotMap() {
        // We'll use a simplified continent shape via dots
        // Using a hardcoded rough continent polygon approach
        const dots = [];
        const step = 0.012; // dot spacing

        // Simplified continents (rough bounding boxes with mask)
        const continents = [
            // North America
            { x1: 0.12, y1: 0.20, x2: 0.32, y2: 0.45 },
            // South America
            { x1: 0.26, y1: 0.55, x2: 0.38, y2: 0.88 },
            // Europe
            { x1: 0.43, y1: 0.22, x2: 0.58, y2: 0.42 },
            // Africa
            { x1: 0.44, y1: 0.42, x2: 0.60, y2: 0.85 },
            // Asia
            { x1: 0.56, y1: 0.20, x2: 0.90, y2: 0.55 },
            // Australia
            { x1: 0.78, y1: 0.65, x2: 0.92, y2: 0.82 }
        ];

        for (let x = 0; x < 1; x += step) {
            for (let y = 0; y < 1; y += step) {
                let inContinent = false;
                for (const c of continents) {
                    if (x >= c.x1 && x <= c.x2 && y >= c.y1 && y <= c.y2) {
                        inContinent = true;
                        break;
                    }
                }
                // Add random gaps for organic feel
                if (inContinent && Math.random() > 0.15) {
                    dots.push({ x, y });
                }
            }
        }
        return dots;
    }

    let dots = generateDotMap();

    // Active attacks
    const attacks = [];
    const MAX_ATTACKS = 12;

    // Counters
    let totalAttacks = 0;
    let criticalAttacks = 0;
    const targetedCountries = new Set();

    // Attack object
    function createAttack() {
        let from, to;
        do {
            from = COUNTRY_KEYS[Math.floor(Math.random() * COUNTRY_KEYS.length)];
            to = COUNTRY_KEYS[Math.floor(Math.random() * COUNTRY_KEYS.length)];
        } while (from === to);

        const type = ATTACK_TYPES[Math.floor(Math.random() * ATTACK_TYPES.length)];

        return {
            from,
            to,
            type: type.name,
            severity: type.severity,
            progress: 0,
            speed: 0.008 + Math.random() * 0.008,
            startTime: Date.now(),
            pulse: 0
        };
    }

    // Pulse effects at endpoints
    const pulses = [];
    function createPulse(countryKey, color) {
        pulses.push({
            country: countryKey,
            time: 0,
            maxTime: 60,
            color
        });
    }

    // Feed
    const feedEl = document.getElementById('attackFeed');

    function addFeedItem(attack) {
        if (!feedEl) return;
        const now = new Date();
        const timeStr = now.toTimeString().substring(0, 8);

        const item = document.createElement('div');
        item.className = 'feed-item ' + attack.severity;
        item.innerHTML = '<span class="time">' + timeStr + '</span>' +
                         '<span class="type">' + attack.type + '</span><br>' +
                         '→ ' + COUNTRIES[attack.from].name + ' → ' + COUNTRIES[attack.to].name;

        feedEl.insertBefore(item, feedEl.firstChild);

        // Limit feed to 30 items
        while (feedEl.children.length > 30) {
            feedEl.removeChild(feedEl.lastChild);
        }
    }

    // Resize handler
    function resize() {
        W = canvas.width = window.innerWidth;
        H = canvas.height = window.innerHeight;
        // Center map on screen, keep aspect ratio
        MAP_SCALE = Math.min(W / 1.4, H / 1.0) * 0.85;
        MAP_OFFSET_X = (W - MAP_SCALE * 1.0) / 2;
        MAP_OFFSET_Y = (H - MAP_SCALE * 1.0) / 2;
    }
    resize();
    window.addEventListener('resize', () => {
        resize();
        dots = generateDotMap();
    });

    // Convert relative coords to canvas coords
    function toCanvas(rx, ry) {
        return {
            x: MAP_OFFSET_X + rx * MAP_SCALE,
            y: MAP_OFFSET_Y + ry * MAP_SCALE * 0.7
        };
    }

    // === RENDER ===
    let lastAttackTime = 0;

    function render(timestamp) {
        ctx.clearRect(0, 0, W, H);

        // 1. Draw dotted world map
        for (const dot of dots) {
            const p = toCanvas(dot.x, dot.y);
            ctx.fillStyle = 'rgba(0, 255, 157, 0.28)';
            ctx.beginPath();
            ctx.arc(p.x, p.y, 1, 0, Math.PI * 2);
            ctx.fill();
        }

        // 2. Draw country nodes (small glowing dots)
        for (const key of COUNTRY_KEYS) {
            const c = COUNTRIES[key];
            const p = toCanvas(c.x, c.y);
            const glowSize = 3 + Math.sin(timestamp * 0.002 + c.x * 10) * 1.5;

            const grd = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, glowSize * 4);
            grd.addColorStop(0, 'rgba(0, 240, 255, 0.9)');
            grd.addColorStop(0.5, 'rgba(0, 240, 255, 0.3)');
            grd.addColorStop(1, 'rgba(0, 240, 255, 0)');

            ctx.fillStyle = grd;
            ctx.beginPath();
            ctx.arc(p.x, p.y, glowSize * 4, 0, Math.PI * 2);
            ctx.fill();

            ctx.fillStyle = '#00f0ff';
            ctx.beginPath();
            ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
            ctx.fill();
        }

        // 3. Draw active attacks
        for (let i = attacks.length - 1; i >= 0; i--) {
            const a = attacks[i];
            a.progress += a.speed;
            a.pulse += 0.15;

            if (a.progress >= 1) {
                attacks.splice(i, 1);
                continue;
            }

            const from = COUNTRIES[a.from];
            const to = COUNTRIES[a.to];
            const p1 = toCanvas(from.x, from.y);
            const p2 = toCanvas(to.x, to.y);

            // Curved path (bezier) for arc effect
            const midX = (p1.x + p2.x) / 2;
            const midY = (p1.y + p2.y) / 2 - Math.abs(p2.x - p1.x) * 0.25;

            // Draw trailing arc (full path in low opacity)
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.quadraticCurveTo(midX, midY, p2.x, p2.y);

            const isCritical = a.severity === 'critical';
            const baseColor = isCritical ? '255, 0, 64' : (a.severity === 'warning' ? '255, 166, 87' : '0, 255, 157');

            ctx.strokeStyle = 'rgba(' + baseColor + ', 0.15)';
            ctx.lineWidth = 1;
            ctx.stroke();

            // Draw animated line up to progress
            // Calculate point at progress
            const t = a.progress;
            const xt = (1 - t) * (1 - t) * p1.x + 2 * (1 - t) * t * midX + t * t * p2.x;
            const yt = (1 - t) * (1 - t) * p1.y + 2 * (1 - t) * t * midY + t * t * p2.y;

            // Full path in bright color up to progress
            // We'll draw linear approximation
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            const steps = 30;
            const upto = Math.floor(steps * a.progress);
            for (let s = 1; s <= upto; s++) {
                const ts = s / steps;
                const xs = (1 - ts) * (1 - ts) * p1.x + 2 * (1 - ts) * ts * midX + ts * ts * p2.x;
                const ys = (1 - ts) * (1 - ts) * p1.y + 2 * (1 - ts) * ts * midY + ts * ts * p2.y;
                ctx.lineTo(xs, ys);
            }

            ctx.strokeStyle = 'rgba(' + baseColor + ', 0.85)';
            ctx.lineWidth = 1.8;
            ctx.shadowBlur = 12;
            ctx.shadowColor = 'rgba(' + baseColor + ', 1)';
            ctx.stroke();
            ctx.shadowBlur = 0;

            // Glowing head at current position
            ctx.beginPath();
            ctx.arc(xt, yt, 3.5, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(' + baseColor + ', 1)';
            ctx.shadowBlur = 20;
            ctx.shadowColor = 'rgba(' + baseColor + ', 1)';
            ctx.fill();
            ctx.shadowBlur = 0;

            // Origin pulse
            const pulseR = 4 + (a.pulse % 1) * 12;
            ctx.beginPath();
            ctx.arc(p1.x, p1.y, pulseR, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(' + baseColor + ', ' + (1 - (a.pulse % 1)) * 0.5 + ')';
            ctx.lineWidth = 1.5;
            ctx.stroke();
        }

        // 4. Random spawning of attacks
        if (attacks.length < MAX_ATTACKS && timestamp - lastAttackTime > 400) {
            const newAttack = createAttack();
            attacks.push(newAttack);
            addFeedItem(newAttack);
            lastAttackTime = timestamp;

            // Update counters
            totalAttacks += Math.floor(Math.random() * 200) + 50;
            if (newAttack.severity === 'critical') {
                criticalAttacks += Math.floor(Math.random() * 5) + 1;
            }
            targetedCountries.add(newAttack.to);

            // Update DOM
            const ac = document.getElementById('attackCounter');
            const cc = document.getElementById('criticalCounter');
            const tc = document.getElementById('countriesCount');
            if (ac) ac.textContent = totalAttacks.toLocaleString();
            if (cc) cc.textContent = criticalAttacks.toLocaleString();
            if (tc) tc.textContent = targetedCountries.size;
        }

        requestAnimationFrame(render);
    }

    // Initial counters
    totalAttacks = 1247683;
    criticalAttacks = 8765;
    targetedCountries.add('USA');
    targetedCountries.add('India');
    targetedCountries.add('UK');

    requestAnimationFrame(render);

    // Initial feed items
    for (let i = 0; i < 5; i++) {
        setTimeout(() => {
            const a = createAttack();
            addFeedItem(a);
        }, i * 200);
    }

    console.log('%c🌍 LIVE CYBER ATTACK MAP ACTIVE', 'color:#ff0040;font-size:16px;font-weight:bold;');
})();
