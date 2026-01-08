#!/usr/bin/env python3
"""
Simple Integration Test for Jarvis AI Assistant
"""

import sys
import time

print("=" * 60)
print("JARVIS AI ASSISTANT - INTEGRATION TEST")
print("=" * 60)

# Test 1: Import all modules
print("\n[TEST 1] Module Imports...")
try:
    import config
    print("[OK] Config imported")
except Exception as e:
    print(f"[FAIL] Config: {e}")
    sys.exit(1)

try:
    from brain import Brain
    print("[OK] Brain imported")
except Exception as e:
    print(f"[FAIL] Brain: {e}")
    sys.exit(1)

try:
    from listen import Listener
    print("[OK] Listener imported")
except Exception as e:
    print(f"[FAIL] Listener: {e}")
    sys.exit(1)

try:
    from speak import Speaker
    print("[OK] Speaker imported")
except Exception as e:
    print(f"[FAIL] Speaker: {e}")
    sys.exit(1)

try:
    import skills
    print("[OK] Skills imported")
except Exception as e:
    print(f"[FAIL] Skills: {e}")
    sys.exit(1)

# Test 2: Configuration
print("\n[TEST 2] Configuration...")
try:
    if config.validate_config():
        print("[OK] Config valid")
        print(f"  Model: {config.MODEL_NAME}")
        print(f"  Wake words: {config.WAKE_WORDS}")
    else:
        print("[FAIL] Config invalid")
        sys.exit(1)
except Exception as e:
    print(f"[FAIL] Config test: {e}")
    sys.exit(1)

# Test 3: Brain
print("\n[TEST 3] Brain System...")
try:
    brain = Brain()
    print("[OK] Brain initialized")
    
    stats = brain.get_stats()
    print(f"  Model: {stats['model']}")
    print(f"  History: {stats['history_length']}")
    
    # Test chat (will fail if Ollama not running)
    try:
        response = brain.chat("Hello test")
        print(f"[OK] AI chat: {response[:30]}...")
    except Exception:
        print("[WARN] AI chat failed (Ollama not running)")
        
except Exception as e:
    print(f"[FAIL] Brain test: {e}")
    sys.exit(1)

# Test 4: Speaker
print("\n[TEST 4] Speaker System...")
try:
    speaker = Speaker(rate=150, volume=0.5)
    print("[OK] Speaker initialized")
    
    stats = speaker.get_stats()
    print(f"  Rate: {stats['current_rate']}")
    print(f"  Volume: {stats['current_volume']}")
    
    # Test speech
    speaker.say("Test complete", block=False)
    print("[OK] Speech queued")
    
except Exception as e:
    print(f"[FAIL] Speaker test: {e}")
    sys.exit(1)

# Test 5: Listener
print("\n[TEST 5] Listener System...")
try:
    listener = Listener()
    print("[OK] Listener initialized")
    
    stats = listener.get_stats()
    print(f"  Calibrated: {stats['calibrated']}")
    print(f"  Energy threshold: {stats['energy_threshold']:.1f}")
    
except Exception as e:
    print(f"[FAIL] Listener test: {e}")
    sys.exit(1)

# Test 6: Skills
print("\n[TEST 6] Skills System...")
try:
    # Test basic skills
    time_result = skills.get_time()
    print(f"[OK] Time skill: {time_result}")
    
    date_result = skills.get_date()
    print(f"[OK] Date skill: {date_result}")
    
    # Count skills
    skill_count = len(skills.SKILLS)
    print(f"[OK] {skill_count} skills available")
    
    # Test some key skills
    key_skills = ['time', 'date', 'open', 'hardware']
    for skill in key_skills:
        if skill in skills.SKILLS:
            print(f"  {skill}: {skills.SKILLS[skill].__name__}")
    
except Exception as e:
    print(f"[FAIL] Skills test: {e}")
    sys.exit(1)

# Test 7: Inter-component communication
print("\n[TEST 7] Communication...")
try:
    # Brain to Speaker
    brain_response = brain.chat("What time is it?")
    speaker.say(brain_response[:30], block=False)
    print("[OK] Brain -> Speaker")
    
    # Skills to Speaker
    skill_response = skills.get_time()
    speaker.say(skill_response, block=False)
    print("[OK] Skills -> Speaker")
    
    print("[OK] All communication working")
    
except Exception as e:
    print(f"[FAIL] Communication test: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("INTEGRATION TEST RESULTS")
print("=" * 60)
print("[OK] All modules imported successfully")
print("[OK] Configuration validated")
print("[OK] Brain system functional")
print("[OK] Speaker system functional")
print("[OK] Listener system functional")
print("[OK] Skills system functional")
print("[OK] Inter-component communication working")
print("\n[SUCCESS] All tests passed!")
print("Jarvis AI Assistant is ready to use.")
print("\nTo start: python main.py")
print("For AI chat: Install Ollama from https://ollama.com/download")
print("=" * 60)
