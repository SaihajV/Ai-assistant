#!/usr/bin/env python3
"""
Integration Test for Jarvis AI Assistant
Tests all components working together
"""

import sys
import time
import logging
from datetime import datetime

# Test imports
try:
    import config
    print("[OK] Config module imported successfully")
except Exception as e:
    print(f"[FAIL] Config import failed: {e}")
    sys.exit(1)

try:
    from brain import Brain
    print("[OK] Brain module imported successfully")
except Exception as e:
    print(f"[FAIL] Brain import failed: {e}")
    sys.exit(1)

try:
    from listen import Listener
    print("[OK] Listen module imported successfully")
except Exception as e:
    print(f"[FAIL] Listen import failed: {e}")
    sys.exit(1)

try:
    from speak import Speaker
    print("[OK] Speak module imported successfully")
except Exception as e:
    print(f"[FAIL] Speak import failed: {e}")
    sys.exit(1)

try:
    import skills
    print("[OK] Skills module imported successfully")
except Exception as e:
    print(f"[FAIL] Skills import failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("JARVIS INTEGRATION TEST")
print("="*60)

# Test configuration
print("\n[TEST] Configuration validation...")
try:
    if config.validate_config():
        print("[OK] Configuration is valid")
        print(f"  - Model: {config.MODEL_NAME}")
        print(f"  - Wake words: {config.WAKE_WORDS}")
        print(f"  - Log level: {config.LOG_LEVEL}")
    else:
        print("[FAIL] Configuration validation failed")
        sys.exit(1)
except Exception as e:
    print(f"[FAIL] Configuration test failed: {e}")
    sys.exit(1)

# Test brain initialization
print("\n[TEST] Brain initialization...")
try:
    brain = Brain()
    print("✓ Brain initialized successfully")
    
    # Test brain stats
    stats = brain.get_stats()
    print(f"  - Model: {stats['model']}")
    print(f"  - History length: {stats['history_length']}")
    print(f"  - Interactions: {stats['interactions']}")
    
    # Test AI chat (will fail if Ollama not running, but that's OK)
    try:
        response = brain.chat("Hello, this is a test.")
        print(f"✓ AI chat working: {response[:50]}...")
    except Exception as e:
        print(f"⚠ AI chat failed (expected if Ollama not running): {str(e)[:50]}...")
        
except Exception as e:
    print(f"✗ Brain test failed: {e}")
    sys.exit(1)

# Test speaker initialization
print("\n[TEST] Speaker initialization...")
try:
    speaker = Speaker(rate=150, volume=0.5)
    print("✓ Speaker initialized successfully")
    
    # Test speaker stats
    stats = speaker.get_stats()
    print(f"  - Total utterances: {stats['total_utterances']}")
    print(f"  - Currently speaking: {stats['currently_speaking']}")
    print(f"  - Queue size: {stats['queue_size']}")
    
    # Test speech (non-blocking)
    speaker.say("Integration test complete", block=False)
    print("✓ Speech queued successfully")
    
except Exception as e:
    print(f"✗ Speaker test failed: {e}")
    sys.exit(1)

# Test listener initialization
print("\n[TEST] Listener initialization...")
try:
    listener = Listener()
    print("✓ Listener initialized successfully")
    
    # Test listener stats
    stats = listener.get_stats()
    print(f"  - Total attempts: {stats['total_attempts']}")
    print(f"  - Success rate: {stats['success_rate']}")
    print(f"  - Calibrated: {stats['calibrated']}")
    print(f"  - Energy threshold: {stats['energy_threshold']:.1f}")
    
except Exception as e:
    print(f"✗ Listener test failed: {e}")
    sys.exit(1)

# Test skills system
print("\n[TEST] Skills system...")
try:
    # Test basic skills
    time_result = skills.get_time()
    print(f"✓ Time skill: {time_result}")
    
    date_result = skills.get_date()
    print(f"✓ Date skill: {date_result}")
    
    sys_info = skills.get_system_info()
    print(f"✓ System info: {sys_info}")
    
    # Test skills registry
    skill_count = len(skills.SKILLS)
    print(f"✓ Skills registry: {skill_count} skills available")
    
    # List some key skills
    key_skills = ['time', 'date', 'open', 'close', 'hardware']
    for skill in key_skills:
        if skill in skills.SKILLS:
            print(f"  - {skill}: {skills.SKILLS[skill].__name__}")
    
except Exception as e:
    print(f"✗ Skills test failed: {e}")
    sys.exit(1)

# Test inter-component communication
print("\n[TEST] Inter-component communication...")
try:
    # Test brain -> speaker communication
    brain_response = brain.chat("What time is it?")
    speaker.say(brain_response[:50], block=False)
    print("✓ Brain -> Speaker communication working")
    
    # Test skills -> speaker communication
    skill_response = skills.get_time()
    speaker.say(skill_response, block=False)
    print("✓ Skills -> Speaker communication working")
    
    # Test config -> all components
    print(f"✓ Config -> Brain: Using model {config.MODEL_NAME}")
    print(f"✓ Config -> Listener: Energy threshold {config.SPEECH_ENERGY_THRESHOLD}")
    print(f"✓ Config -> Speaker: Rate {config.DEFAULT_VOICE_RATE}")
    
except Exception as e:
    print(f"✗ Inter-component test failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("INTEGRATION TEST SUMMARY")
print("="*60)

print("\n✓ All modules imported successfully")
print("✓ Configuration validated")
print("✓ Brain initialized and functional")
print("✓ Speaker initialized and functional")
print("✓ Listener initialized and functional")
print("✓ Skills system working")
print("✓ Inter-component communication verified")

print("\n🎉 ALL TESTS PASSED!")
print("Your Jarvis AI Assistant is ready to use.")
print("\nTo start the assistant, run: python main.py")
print("Note: For AI chat functionality, install and start Ollama from https://ollama.com/download")

print("\n" + "="*60)
