import { useEffect, useRef, useCallback, useState } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { VRMLoaderPlugin, VRM, VRMExpressionPresetName } from '@pixiv/three-vrm';
import { useStore } from '@/hooks/useStore';

interface VRMSceneState {
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  clock: THREE.Clock;
  vrm: VRM | null;
  mixer: THREE.AnimationMixer | null;
  raycaster: THREE.Raycaster;
  mouse: THREE.Vector2;
  lipSyncTarget: number;
  blinkTimer: number;
  blinkState: boolean;
  lookTarget: THREE.Vector3;
  lookTimer: number;
  idleTimer: number;
  currentExpression: string;
  expressionTimer: number;
  actions: { name: string; startTime: number; duration: number }[];
  // Advanced camera tracking
  cameraTrackingEnabled: boolean;
  lastCameraPos: THREE.Vector3;
  lastCameraRot: THREE.Euler;
  vrmTargetPosition?: THREE.Vector3 | null;
  vrmMoveSpeed?: number;
  vrmBaseY?: number;
}

export default function VRMViewerAdvanced() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<VRMSceneState | null>(null);
  const trackingIntervalRef = useRef<number | null>(null);
  const [stats, setStats] = useState({ fps: 0, tracking: false });

  // Send camera tracking data to backend
  const sendCameraTracking = useCallback((camera: THREE.PerspectiveCamera) => {
    if (!sceneRef.current?.vrm) return;

    const trackingData = {
      position_x: camera.position.x,
      position_y: camera.position.y,
      position_z: camera.position.z,
      rotation_x: camera.rotation.x,
      rotation_y: camera.rotation.y,
      rotation_z: camera.rotation.z,
      fov: camera.fov,
      distance_to_model: camera.position.distanceTo(sceneRef.current.vrm.scene.position),
      angle_to_model: Math.atan2(camera.position.x, camera.position.z),
    };

    // Send to backend via WebSocket if available
    const ws = (window as any).sarahWS;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'camera_tracking',
        data: trackingData,
      }));
    }

    return trackingData;
  }, []);

  // Setup real-time camera tracking
  const setupCameraTracking = useCallback(() => {
    if (!sceneRef.current) return;
    
    const s = sceneRef.current;
    
    trackingIntervalRef.current = window.setInterval(() => {
      if (s.cameraTrackingEnabled) {
        sendCameraTracking(s.camera);
      }
    }, 50); // Send tracking data every 50ms (20 FPS tracking)

    setStats(p => ({ ...p, tracking: true }));
  }, [sendCameraTracking]);

  const initScene = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a12);
    scene.fog = new THREE.Fog(0x0a0a12, 8, 20);

    // Ground
    const groundGeo = new THREE.PlaneGeometry(30, 30);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x1a1a2e,
      roughness: 0.8,
      metalness: 0.2,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    scene.add(ground);

    // Grid
    const grid = new THREE.GridHelper(20, 20, 0xff3366, 0x222244);
    grid.position.y = 0.01;
    scene.add(grid);

    // Camera
    const camera = new THREE.PerspectiveCamera(35, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.set(0, 1.4, 3.5);

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 1.3, 0);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 1.5;
    controls.maxDistance = 6;
    controls.minPolarAngle = 0.3;
    controls.maxPolarAngle = Math.PI / 2 - 0.05;
    controls.enablePan = false;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(3, 5, 3);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 1024;
    dirLight.shadow.mapSize.height = 1024;
    scene.add(dirLight);

    const rimLight = new THREE.DirectionalLight(0xff6b9d, 0.5);
    rimLight.position.set(-2, 3, -2);
    scene.add(rimLight);

    const fillLight = new THREE.PointLight(0x9d4edd, 0.3, 10);
    fillLight.position.set(-2, 2, 2);
    scene.add(fillLight);

    // Particle system
    const particleCount = 50;
    const particles = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 10;
      positions[i * 3 + 1] = Math.random() * 4;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 10;
    }
    particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMat = new THREE.PointsMaterial({
      color: 0xff3366,
      size: 0.02,
      transparent: true,
      opacity: 0.6,
    });
    const particleSystem = new THREE.Points(particles, particleMat);
    scene.add(particleSystem);

    sceneRef.current = {
      renderer,
      scene,
      camera,
      controls,
      clock: new THREE.Clock(),
      vrm: null,
      mixer: null,
      raycaster: new THREE.Raycaster(),
      mouse: new THREE.Vector2(),
      lipSyncTarget: 0,
      blinkTimer: 0,
      blinkState: false,
      lookTarget: new THREE.Vector3(0, 1.6, 3),
      lookTimer: 0,
      idleTimer: 0,
      currentExpression: 'neutral',
      expressionTimer: 0,
      actions: [],
      cameraTrackingEnabled: true,
      lastCameraPos: camera.position.clone(),
      lastCameraRot: camera.rotation.clone() as THREE.Euler,
    };

    // Load VRM
    loadVRM();

    // Start animation loop
    animate();

    // Setup camera tracking
    setupCameraTracking();

    // Event listeners
    window.addEventListener('resize', onResize);
    window.addEventListener('vrm-expression', onExpressionEvent as EventListener);
    window.addEventListener('vrm-animation', onAnimationEvent as EventListener);
    window.addEventListener('vrm-lipsync', onLipSyncEvent as EventListener);
    window.addEventListener('vrm-outfit-change', onOutfitChange as EventListener);
    window.addEventListener('pet-move', onPetMove as EventListener);
    window.addEventListener('vrm-camera-reaction', onCameraReaction as EventListener);

    // Click handler for body interactions
    canvas.addEventListener('click', onCanvasClick);

    return () => {
      if (trackingIntervalRef.current) {
        clearInterval(trackingIntervalRef.current);
      }
      window.removeEventListener('resize', onResize);
      window.removeEventListener('vrm-expression', onExpressionEvent as EventListener);
      window.removeEventListener('vrm-animation', onAnimationEvent as EventListener);
      window.removeEventListener('vrm-lipsync', onLipSyncEvent as EventListener);
      window.removeEventListener('vrm-outfit-change', onOutfitChange as EventListener);
      window.removeEventListener('pet-move', onPetMove as EventListener);
      window.removeEventListener('vrm-camera-reaction', onCameraReaction as EventListener);
      canvas.removeEventListener('click', onCanvasClick);
      renderer.dispose();
    };
  }, [setupCameraTracking]);

  // Placeholder event handlers - they'll be defined below
  const onExpressionEvent = (e: CustomEvent) => {
    if (!sceneRef.current?.vrm?.expressionManager) return;
    const expr = e.detail as string;
    sceneRef.current.currentExpression = expr;
    sceneRef.current.expressionTimer = 3;
    sceneRef.current.vrm.expressionManager.setValue(expr as VRMExpressionPresetName, 1);
  };

  const onAnimationEvent = (e: CustomEvent) => {
    if (!sceneRef.current) return;
    const anim = e.detail as string;
    const durationMap: Record<string, number> = {
      wave: 2, kiss: 2, hug: 3, punch: 0.8, kick: 1,
      dance: 4, jump: 1, bow: 1.5, clap: 2, spin: 1.5,
      nod: 1, shake_head: 1
    };
    sceneRef.current.actions.push({
      name: anim,
      startTime: sceneRef.current.clock.getElapsedTime(),
      duration: durationMap[anim] || 1
    });
  };

  const onLipSyncEvent = (e: CustomEvent) => {
    if (!sceneRef.current) return;
    sceneRef.current.lipSyncTarget = e.detail as number;
  };

  const onOutfitChange = (e: CustomEvent) => {
    const detail = e.detail as any;
    const outfitPath = detail?.outfitData?.path || detail?.path;
    if (outfitPath) {
      loadVRMModel(outfitPath, 'fade');
    }
  };

  const onPetMove = (e: CustomEvent) => {
    if (!sceneRef.current) return;
    const detail = e.detail as any;
    sceneRef.current.vrmTargetPosition = new THREE.Vector3(detail?.x ?? 0, detail?.y ?? 0, detail?.z ?? 0);
    sceneRef.current.vrmMoveSpeed = detail?.speed ?? 1.5;
    sceneRef.current.vrmBaseY = sceneRef.current.vrm?.scene?.position?.y ?? 0;
  };

  const onCameraReaction = (e: CustomEvent) => {
    const detail = e.detail as any;
    if (detail.action === 'look_at_camera') {
      // Model should look at camera
    } else if (detail.action === 'turn_around') {
      // Model should turn around
    } else if (detail.action === 'dodge') {
      // Model should dodge
    }
  };

  const onCanvasClick = (e: MouseEvent) => {
    if (!sceneRef.current?.vrm) return;
    const s = sceneRef.current;
    s.mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
    s.mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
    s.raycaster.setFromCamera(s.mouse, s.camera);

    if (!s.vrm) return;
    const intersects = s.raycaster.intersectObjects(s.vrm.scene.children, true);
    if (intersects.length > 0) {
      const point = intersects[0].point;
      const localY = point.y - s.vrm.scene.position.y;

      // Determine body part
      let part = 'body';
      if (localY > 1.7) part = 'head';
      else if (localY > 1.5) part = 'face';
      else if (localY > 1.3) part = 'hair';
      else if (localY > 1.1) part = 'shoulder';
      else if (localY > 0.9) part = 'chest';
      else if (localY > 0.7) part = 'stomach';
      else if (localY > 0.4) part = 'hand';
      else part = 'leg';

      // Send body interaction to backend
      const ws = (window as any).sarahWS;
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'vrm_body_interaction',
          body_part: part,
          timestamp: Date.now(),
        }));
      }

      // Trigger reaction animation
      window.dispatchEvent(new CustomEvent('vrm-body-touched', { detail: { part } }));
    }
  };

  const onResize = () => {
    if (!sceneRef.current) return;
    const { camera, renderer } = sceneRef.current;
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  };

  const setObjectOpacity = (object: THREE.Object3D, opacity: number) => {
    object.traverse((child: any) => {
      if (child.material) {
        const materials = Array.isArray(child.material) ? child.material : [child.material];
        materials.forEach((material: any) => {
          if (material) {
            material.transparent = true;
            material.opacity = opacity;
          }
        });
      }
    });
  };

  const loadVRMModel = useCallback((modelPath: string, transitionType: 'fade' | 'cut' = 'fade') => {
    if (!sceneRef.current) return;
    const { scene } = sceneRef.current;
    const oldVrm = sceneRef.current.vrm;

    if (transitionType === 'fade' && oldVrm) {
      setObjectOpacity(oldVrm.scene, 0);
    }

    const loader = new GLTFLoader();
    loader.register((parser) => new VRMLoaderPlugin(parser));

    loader.load(
      modelPath,
      (gltf) => {
        const vrm = gltf.userData.vrm as VRM;

        if (oldVrm) {
          scene.remove(oldVrm.scene);
        }

        sceneRef.current!.vrm = vrm;
        scene.add(vrm.scene);

        vrm.scene.rotation.y = Math.PI;

        const rArm = vrm.humanoid.getNormalizedBoneNode('rightUpperArm');
        const lArm = vrm.humanoid.getNormalizedBoneNode('leftUpperArm');
        if (rArm) rArm.rotation.z = -1.2;
        if (lArm) lArm.rotation.z = 1.2;

        if (vrm.lookAt) {
          vrm.lookAt.target = sceneRef.current!.camera;
        }

        sceneRef.current!.mixer = new THREE.AnimationMixer(vrm.scene);

        if (transitionType === 'fade') {
          setObjectOpacity(vrm.scene, 0);
          requestAnimationFrame(function fadeStep() {
            const currentOpacity = (vrm.scene as any).userData?.opacity ?? 0;
            const nextOpacity = Math.min(1, currentOpacity + 0.06);
            setObjectOpacity(vrm.scene, nextOpacity);
            (vrm.scene as any).userData = { opacity: nextOpacity };
            if (nextOpacity < 1) {
              requestAnimationFrame(fadeStep);
            }
          });
        }

        useStore.getState().vrmState = { currentVrm: vrm };
        console.log('[VRM]: Model loaded', modelPath);
      },
      undefined,
      (error) => {
        console.error('[VRM]: Load error:', error);
      }
    );
  }, []);

  const loadVRM = () => {
    loadVRMModel('/static/models/sarah.vrm');
  };

  const animate = () => {
    if (!sceneRef.current) return;
    requestAnimationFrame(animate);

    const s = sceneRef.current;
    const delta = s.clock.getDelta();
    const elapsed = s.clock.getElapsedTime();

    s.controls.update();

    if (s.vrm) {
      s.vrm.update(delta);

      // Breathing
      const spine = s.vrm.humanoid.getNormalizedBoneNode('spine');
      if (spine) {
        spine.rotation.x = Math.sin(elapsed * 1.5) * 0.015;
      }

      // Sway
      const chest = s.vrm.humanoid.getNormalizedBoneNode('chest');
      if (chest) {
        chest.rotation.z = Math.sin(elapsed * 0.8) * 0.01;
      }

      // Blinking
      s.blinkTimer -= delta;
      if (s.blinkTimer <= 0) {
        s.blinkState = !s.blinkState;
        s.blinkTimer = s.blinkState ? 0.15 : 2 + Math.random() * 3;
      }
      if (s.vrm.expressionManager) {
        s.vrm.expressionManager.setValue('blink' as VRMExpressionPresetName, s.blinkState ? 1 : 0);
      }

      // Lip sync
      if (s.vrm.expressionManager && s.lipSyncTarget > 0) {
        s.vrm.expressionManager.setValue('aa' as VRMExpressionPresetName, s.lipSyncTarget);
        s.lipSyncTarget *= 0.9;
      }

      // Pet locomotion
      if (s.vrmTargetPosition && s.vrm) {
        const target = s.vrmTargetPosition;
        const pos = s.vrm.scene.position;
        const dir = new THREE.Vector3().subVectors(target, pos);
        const dist = dir.length();
        if (dist > 0.05) {
          const speed = s.vrmMoveSpeed || 1.5;
          const step = Math.min(dist, speed * delta);
          dir.normalize();
          pos.addScaledVector(dir, step);
          const yaw = Math.atan2(dir.x, dir.z);
          s.vrm.scene.rotation.y = Math.PI + yaw;
          const baseY = s.vrmBaseY ?? pos.y;
          pos.y = baseY + Math.sin(elapsed * 8) * 0.02;
        } else {
          s.vrmTargetPosition = null;
          if (s.vrm) s.vrm.scene.position.y = s.vrmBaseY ?? s.vrm.scene.position.y;
        }
      }

      // Particle animation
      s.scene.traverse((obj: THREE.Object3D) => {
        if (obj instanceof THREE.Points) {
          const positions = obj.geometry.attributes.position.array as Float32Array;
          for (let i = 0; i < positions.length; i += 3) {
            positions[i + 1] += Math.sin(elapsed + positions[i]) * 0.002;
            if (positions[i + 1] > 4) positions[i + 1] = 0;
          }
          obj.geometry.attributes.position.needsUpdate = true;
        }
      });
    }

    s.renderer.render(s.scene, s.camera);
  };

  useEffect(() => {
    initScene();
  }, [initScene]);

  return (
    <div className="w-full h-screen relative">
      <canvas ref={canvasRef} className="w-full h-full" />
      <div className="absolute top-2 left-2 text-xs text-white/40 pointer-events-none">
        <div>Tracking: {stats.tracking ? 'ON' : 'OFF'}</div>
      </div>
    </div>
  );
}
