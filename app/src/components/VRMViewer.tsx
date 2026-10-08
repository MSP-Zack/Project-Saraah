import { useEffect, useRef, useCallback } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { VRMLoaderPlugin, VRM, VRMExpressionPresetName } from '@pixiv/three-vrm';
import { useStore } from '@/hooks/useStore';

export default function VRMViewer() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<{
    renderer: THREE.WebGLRenderer;
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    controls: OrbitControls;
    clock: THREE.Clock;
    vrm: VRM | null;
    mixer: THREE.AnimationMixer | null;
    fbxPreview: { root: THREE.Group; mixer: THREE.AnimationMixer } | null;
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
    vrmTargetPosition: THREE.Vector3 | null;
    vrmMoveSpeed: number;
    vrmBaseY: number;
  } | null>(null);

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
      fbxPreview: null,
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
      // Movement/locomotion state for pets
      vrmTargetPosition: null,
      vrmMoveSpeed: 0,
      vrmBaseY: 0,
    };

    // Load VRM
    loadVRM();

    // Start animation loop
    animate();

    // Event listeners
    window.addEventListener('resize', onResize);
    window.addEventListener('vrm-expression', onExpressionEvent as EventListener);
    window.addEventListener('vrm-animation', onAnimationEvent as EventListener);
    window.addEventListener('vrm-lipsync', onLipSyncEvent as EventListener);
    window.addEventListener('vrm-outfit-change', onOutfitChange as EventListener);
    // Pet locomotion events (detail: { x, y, z, speed })
    window.addEventListener('pet-move', onPetMove as EventListener);
    window.addEventListener('fbx-animation-test', onFBXAnimationTest as EventListener);
    window.addEventListener('fbx-animation-clear', onFBXAnimationClear as EventListener);

    // Click handler for body interactions
    canvas.addEventListener('click', onCanvasClick);

    return () => {
      window.removeEventListener('resize', onResize);
      window.removeEventListener('vrm-expression', onExpressionEvent as EventListener);
      window.removeEventListener('vrm-animation', onAnimationEvent as EventListener);
      window.removeEventListener('vrm-lipsync', onLipSyncEvent as EventListener);
      window.removeEventListener('vrm-outfit-change', onOutfitChange as EventListener);
      window.removeEventListener('pet-move', onPetMove as EventListener);
      window.removeEventListener('fbx-animation-test', onFBXAnimationTest as EventListener);
      window.removeEventListener('fbx-animation-clear', onFBXAnimationClear as EventListener);
      canvas.removeEventListener('click', onCanvasClick);
      renderer.dispose();
    };
  }, []);

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

        // Setup VRM
        vrm.scene.rotation.y = Math.PI;

        // Fix arm positions
        const rArm = vrm.humanoid.getNormalizedBoneNode('rightUpperArm');
        const lArm = vrm.humanoid.getNormalizedBoneNode('leftUpperArm');
        if (rArm) rArm.rotation.z = -1.2;
        if (lArm) lArm.rotation.z = 1.2;

        // Setup lookAt
        if (vrm.lookAt) {
          vrm.lookAt.target = sceneRef.current!.camera;
        }

        // Create animation mixer
        sceneRef.current!.mixer = new THREE.AnimationMixer(vrm.scene);

        // Fade in
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

        // Update store
        useStore.getState().vrmState.currentVrm = vrm;

        console.log('[VRM]: Model loaded successfully', modelPath);
      },
      (progress) => {
        const p = Math.round((progress.loaded / progress.total) * 100);
        console.log(`[VRM]: Loading... ${p}%`);
      },
      (error) => {
        console.error('[VRM]: Load error:', error);
      }
    );
  }, []);

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
    const tx = detail?.x ?? 0;
    const ty = detail?.y ?? 0;
    const tz = detail?.z ?? 0;
    sceneRef.current.vrmTargetPosition = new THREE.Vector3(tx, ty, tz);
    sceneRef.current.vrmMoveSpeed = detail?.speed ?? 1.5;
    sceneRef.current.vrmBaseY = sceneRef.current.vrm?.scene?.position?.y ?? 0;
  };

  const loadVRM = () => {
    if (!sceneRef.current) return;
    const { scene } = sceneRef.current;

    const loader = new GLTFLoader();
    loader.register((parser) => new VRMLoaderPlugin(parser));

    loader.load(
      '/static/models/sarah.vrm',
      (gltf) => {
        const vrm = gltf.userData.vrm as VRM;
        sceneRef.current!.vrm = vrm;
        scene.add(vrm.scene);

        // Setup VRM
        vrm.scene.rotation.y = Math.PI;

        // Fix arm positions
        const rArm = vrm.humanoid.getNormalizedBoneNode('rightUpperArm');
        const lArm = vrm.humanoid.getNormalizedBoneNode('leftUpperArm');
        if (rArm) rArm.rotation.z = -1.2;
        if (lArm) lArm.rotation.z = 1.2;

        // Setup lookAt
        if (vrm.lookAt) {
          vrm.lookAt.target = sceneRef.current!.camera;
        }

        // Create animation mixer
        sceneRef.current!.mixer = new THREE.AnimationMixer(vrm.scene);

        // Update store
        useStore.getState().vrmState.currentVrm = vrm;

        console.log('[VRM]: Model loaded successfully');
      },
      (progress) => {
        const p = Math.round((progress.loaded / progress.total) * 100);
        console.log(`[VRM]: Loading... ${p}%`);
      },
      (error) => {
        console.error('[VRM]: Load error:', error);
      }
    );
  };

  const animate = () => {
    if (!sceneRef.current) return;
    requestAnimationFrame(animate);

    const s = sceneRef.current;
    const delta = s.clock.getDelta();
    const elapsed = s.clock.getElapsedTime();

    s.controls.update();

    if (s.vrm) {
      // Update VRM
      s.vrm.update(delta);

      // Breathing animation
      const spine = s.vrm.humanoid.getNormalizedBoneNode('spine');
      if (spine) {
        spine.rotation.x = Math.sin(elapsed * 1.5) * 0.015;
      }

      // Subtle sway
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

      // Idle eye movement
      s.lookTimer -= delta;
      if (s.lookTimer <= 0) {
        s.lookTarget.set(
          (Math.random() - 0.5) * 0.5,
          1.5 + Math.random() * 0.3,
          3 + Math.random() * 0.5
        );
        s.lookTimer = 2 + Math.random() * 4;
      }
      if (s.vrm.lookAt) {
        const currentTarget = s.vrm.lookAt.target;
        if (currentTarget && currentTarget.position) {
          // Smooth look interpolation would go here
        }
      }

      // Lip sync
      if (s.vrm.expressionManager && s.lipSyncTarget > 0) {
        const visemeName = `aa` as VRMExpressionPresetName;
        s.vrm.expressionManager.setValue(visemeName, s.lipSyncTarget);
        s.lipSyncTarget *= 0.9; // Decay
      }

      // Pet locomotion: move VRM root toward a target position if set
      if (s.vrmTargetPosition && s.vrm) {
        const target = s.vrmTargetPosition as THREE.Vector3;
        const pos = s.vrm.scene.position;
        const dir = new THREE.Vector3().subVectors(target, pos);
        const dist = dir.length();
        if (dist > 0.05) {
          const speed = s.vrmMoveSpeed || 1.5;
          const step = Math.min(dist, speed * delta);
          dir.normalize();
          pos.addScaledVector(dir, step);
          // Rotate to face movement direction
          const yaw = Math.atan2(dir.x, dir.z);
          s.vrm.scene.rotation.y = Math.PI + yaw;
          // Simple bobbing during walk
          const baseY = s.vrmBaseY ?? pos.y;
          pos.y = baseY + Math.sin(elapsed * 8) * 0.02;
        } else {
          s.vrmTargetPosition = null;
          if (s.vrm) s.vrm.scene.position.y = s.vrmBaseY ?? s.vrm.scene.position.y;
        }
      }

      // Process animation actions
      s.actions = s.actions.filter((action) => {
        const elapsed_action = elapsed - action.startTime;
        if (elapsed_action > action.duration) {
          // Reset pose after animation
          resetPose(s.vrm!);
          return false;
        }
        applyAnimation(s.vrm!, action.name, elapsed_action, action.duration);
        return true;
      });

      // Expression handling
      if (s.vrm.expressionManager) {
        // Reset expressions
        const expressions = ['happy', 'sad', 'angry', 'relaxed', 'surprised', 'neutral'];
        expressions.forEach((e) => {
          const val = s.vrm!.expressionManager!.getValue(e as VRMExpressionPresetName) || 0;
          if (val > 0) {
            s.vrm!.expressionManager!.setValue(e as VRMExpressionPresetName, Math.max(0, val - delta * 2));
          }
        });

        // Keep current expression active
        if (s.currentExpression !== 'neutral') {
          s.expressionTimer -= delta;
          const intensity = Math.min(1, s.expressionTimer > 0 ? 1 : Math.max(0, s.expressionTimer + 1));
          s.vrm.expressionManager.setValue(s.currentExpression as VRMExpressionPresetName, intensity);
        }
      }
    }

    if (s.fbxPreview) {
      s.fbxPreview.mixer.update(delta);
    }

    // Animate particles
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

    s.renderer.render(s.scene, s.camera);
  };

  const resetPose = (vrm: VRM) => {
    const rArm = vrm.humanoid.getNormalizedBoneNode('rightUpperArm');
    const lArm = vrm.humanoid.getNormalizedBoneNode('leftUpperArm');
    const head = vrm.humanoid.getNormalizedBoneNode('head');
    const spine = vrm.humanoid.getNormalizedBoneNode('spine');
    if (rArm) rArm.rotation.z = -1.2;
    if (lArm) lArm.rotation.z = 1.2;
    if (head) {
      head.rotation.x = 0;
      head.rotation.y = 0;
      head.rotation.z = 0;
    }
    if (spine) {
      spine.rotation.x = 0;
      spine.rotation.y = 0;
      spine.rotation.z = 0;
    }
    // restore base Y if available
    if (sceneRef.current && sceneRef.current.vrmBaseY !== undefined && sceneRef.current.vrm) {
      sceneRef.current.vrm.scene.position.y = sceneRef.current.vrmBaseY;
    }
  };

  const applyAnimation = (vrm: VRM, name: string, elapsed: number, duration: number) => {
    const progress = elapsed / duration;
    const rArm = vrm.humanoid.getNormalizedBoneNode('rightUpperArm');
    const lArm = vrm.humanoid.getNormalizedBoneNode('leftUpperArm');
    const head = vrm.humanoid.getNormalizedBoneNode('head');

    switch (name) {
      case 'wave':
        if (rArm) rArm.rotation.z = -2.5 + Math.sin(progress * Math.PI * 4) * 0.3;
        break;
      case 'kiss':
        if (rArm) rArm.rotation.z = -0.5;
        if (head) head.rotation.x = -0.2;
        break;
      case 'hug':
        if (rArm) rArm.rotation.z = -0.3;
        if (lArm) lArm.rotation.z = 0.3;
        break;
      case 'punch':
        if (rArm) rArm.rotation.z = -1.2 - Math.sin(progress * Math.PI) * 0.8;
        break;
      case 'kick':
        // Simple leg raise
        break;
      case 'dance':
        if (rArm) rArm.rotation.z = -1.2 + Math.sin(elapsed * 8) * 0.5;
        if (lArm) lArm.rotation.z = 1.2 - Math.sin(elapsed * 8) * 0.5;
        break;
      case 'jump':
        vrm.scene.position.y = Math.sin(progress * Math.PI) * 0.3;
        if (rArm) rArm.rotation.z = -2.5;
        if (lArm) lArm.rotation.z = 2.5;
        break;
      case 'sleep':
        // subtle breathing while sleeping and head tilt
        if (head) head.rotation.x = -0.45 + Math.sin(progress * Math.PI * 2) * 0.02;
        if (rArm) rArm.rotation.z = -1.0;
        if (lArm) lArm.rotation.z = 1.0;
        // tiny bob for breathing
        vrm.scene.position.y = (sceneRef.current?.vrmBaseY ?? vrm.scene.position.y) + Math.sin(progress * Math.PI * 2) * 0.005;
        break;
      case 'sit':
        // simple sit pose by rotating the spine and relaxing arms
        const spine = vrm.humanoid.getNormalizedBoneNode('spine');
        if (spine) spine.rotation.x = -0.25 * Math.sin(progress * Math.PI);
        if (rArm) rArm.rotation.z = -1.0;
        if (lArm) lArm.rotation.z = 1.0;
        break;
      case 'bow':
        const spineNode = vrm.humanoid.getNormalizedBoneNode('spine');
        if (spineNode) spineNode.rotation.x = 0.5 * Math.sin(progress * Math.PI);
        break;
      case 'clap':
        if (rArm) rArm.rotation.z = -0.3 + Math.sin(progress * Math.PI * 6) * 0.1;
        if (lArm) lArm.rotation.z = 0.3 - Math.sin(progress * Math.PI * 6) * 0.1;
        break;
      case 'spin':
        vrm.scene.rotation.y = Math.PI + progress * Math.PI * 2;
        break;
      case 'nod':
        if (head) head.rotation.x = Math.sin(progress * Math.PI * 3) * 0.15;
        break;
      case 'shake_head':
        if (head) head.rotation.y = Math.sin(progress * Math.PI * 4) * 0.15;
        break;
    }
  };

  const onResize = () => {
    if (!sceneRef.current) return;
    const { camera, renderer } = sceneRef.current;
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  };

  const onExpressionEvent = (e: CustomEvent) => {
    if (!sceneRef.current?.vrm?.expressionManager) return;
    const expr = e.detail as string;
    sceneRef.current.currentExpression = expr;
    sceneRef.current.expressionTimer = 3; // Expression lasts 3 seconds
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

  const disposeFBXPreview = () => {
    const state = sceneRef.current;
    if (!state?.fbxPreview) return;
    state.scene.remove(state.fbxPreview.root);
    state.fbxPreview.root.traverse((child) => {
      const mesh = child as THREE.Mesh;
      if (mesh.geometry) mesh.geometry.dispose();
      const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      materials.forEach((material) => material?.dispose());
    });
    state.fbxPreview = null;
  };

  const onFBXAnimationTest = (e: CustomEvent) => {
    if (!sceneRef.current) return;
    const detail = e.detail as { url?: string; clipName?: string };
    if (!detail?.url) return;

    const loader = new FBXLoader();
    loader.load(
      detail.url,
      (object) => {
        const state = sceneRef.current;
        if (!state) return;
        disposeFBXPreview();

        const bounds = new THREE.Box3().setFromObject(object);
        const size = bounds.getSize(new THREE.Vector3());
        const center = bounds.getCenter(new THREE.Vector3());
        const scale = size.y > 0 ? 2.4 / size.y : 0.01;
        object.scale.setScalar(scale);
        object.position.set(-center.x * scale, -bounds.min.y * scale, -center.z * scale);

        const mixer = new THREE.AnimationMixer(object);
        const clip = object.animations.find((candidate) => candidate.name === detail.clipName) || object.animations[0];
        if (clip) {
          mixer.clipAction(clip).reset().setLoop(THREE.LoopRepeat, Infinity).play();
        }
        state.fbxPreview = { root: object, mixer };
        state.scene.add(object);
        if (state.vrm) state.vrm.scene.visible = false;
        console.log('[FBX TEST]: Playing', clip?.name || 'no animation clip', detail.url);
      },
      undefined,
      (error) => console.error('[FBX TEST]: Load error', error),
    );
  };

  const onFBXAnimationClear = () => {
    const state = sceneRef.current;
    if (!state) return;
    disposeFBXPreview();
    if (state.vrm) state.vrm.scene.visible = true;
  };

  const onLipSyncEvent = (e: CustomEvent) => {
    if (!sceneRef.current) return;
    sceneRef.current.lipSyncTarget = e.detail as number;
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

      // Send to server
      const ws = (window as any).sarahWS;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'vrm_body_click', part }));
      }

      // Visual feedback
      if (s.vrm.expressionManager) {
        s.vrm.expressionManager.setValue('happy' as VRMExpressionPresetName, 0.8);
        setTimeout(() => {
          if (s.vrm?.expressionManager) {
            s.vrm.expressionManager.setValue('happy' as VRMExpressionPresetName, 0);
          }
        }, 500);
      }
    }
  };

  useEffect(() => {
    const cleanup = initScene();
    return cleanup;
  }, [initScene]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 1,
      }}
    />
  );
}
