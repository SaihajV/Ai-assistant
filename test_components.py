#!/usr/bin/env python3
"""
Test script for Jarvis AI Assistant
Tests individual components to ensure they work correctly
"""

import sys
import time
import logging
from datetime import datetime

# Import Jarvis components
import config
from brain import Brain
from listen import Listener
from speak import Speaker
import skills

def setup_logging():
    """Setup logging for tests"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def test_config():
    """Test configuration loading"""
    print("[TEST] Testing configuration...")
    try:
        valid = config.validate_config()
        print(f"[OK] Configuration valid: {valid}")
        print(f"[INFO] Model: {config.MODEL_NAME}")
        print(f"[INFO] Wake words: {config.WAKE_WORDS}")
        return True
    except Exception as e:
        print(f"[FAIL] Configuration error: {e}")
        return False

def test_brain():
    """Test AI brain functionality"""
    print("\n[TEST] Testing AI brain...")
    try:
        brain = Brain()
        print("[OK] Brain initialized")
        
        # Test basic chat (may fail if Ollama not running)
        try:
            response = brain.chat("Hello, can you hear me?")
            print(f"[OK] Brain response: {response[:50]}...")
        except Exception as e:
            print(f"[WARN] Brain chat failed (Ollama may not be running): {e}")
        
        # Test stats
        stats = brain.get_stats()
        print(f"[OK] Brain stats: {stats}")
        return True
    except Exception as e:
        print(f"[FAIL] Brain error: {e}")
        return False

def test_speaker():
    """Test text-to-speech"""
    print("\n[TEST] Testing speaker...")
    try:
        speaker = Speaker(rate=150, volume=0.5)
        print("[OK] Speaker initialized")
        
        # Test speech (non-blocking)
        speaker.say("System test complete", block=False)
        print("[OK] Speech queued")
        
        # Wait a moment for speech to start
        time.sleep(1)
        
        # Test stats
        stats = speaker.get_stats()
        print(f"[OK] Speaker stats: {stats}")
        return True
    except Exception as e:
        print(f"[FAIL] Speaker error: {e}")
        return False

def test_listener():
    """Test speech recognition (quick test)"""
    print("\n[TEST] Testing listener...")
    try:
        listener = Listener()
        print("[OK] Listener initialized")
        
        # Test stats
        stats = listener.get_stats()
        print(f"[OK] Listener stats: {stats}")
        return True
    except Exception as e:
        print(f"[FAIL] Listener error: {e}")
        return False

def test_skills():
    """Test skill system"""
    print("\n[TEST] Testing skills...")
    try:
        # Test time skill
        time_result = skills.get_time()
        print(f"[OK] Time skill: {time_result}")
        
        # Test date skill
        date_result = skills.get_date()
        print(f"[OK] Date skill: {date_result}")
        
        # Test system info
        sys_info = skills.get_system_info()
        print(f"[OK] System info: {sys_info}")
        
        # List all skills
        skill_list = skills.list_skills()
        print(f"[OK] Available skills: {len(skill_list)} skills")
        return True
    except Exception as e:
        print(f"[FAIL] Skills error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("[JARVIS] COMPONENT TEST SUITE")
    print("=" * 60)
    
    setup_logging()
    
    tests = [
        ("Configuration", test_config),
        ("Skills", test_skills),
        ("Speaker", test_speaker),
        ("Listener", test_listener),
        ("Brain", test_brain),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[FAIL] {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("[SUMMARY] TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:12} : {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("[SUCCESS] All components working!")
        return 0
    else:
        print("[WARNING] Some components have issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
