import sys, os
sys.path.insert(0, r'c:\Users\krishna\.gemini\antigravity\scratch\bruh\backend')

from app.ml.hybrid_orchestrator import HybridOrchestrator

orc = HybridOrchestrator()

print('=== TEST 1: Common Cold (fever + sore throat, 2 days) ===')
r = orc.predict(age=25, gender=1, severity=1, duration_days=2,
    clinical_symptoms='I have a sore throat, runny nose and mild fever',
    fever=True, sore_throat=True)
names = [c['name'] for c in r['likely_conditions']]
print('Conditions:', names)
print('Blacklist applied:', r['blacklist_applied'])
print('Rules:', r['rules_applied'])
print('Risk:', r['risk_level'], '| Urgency:', r['urgency'])
print()

print('=== TEST 2: Blacklist — high-severity blocked at 3 days ===')
r2 = orc.predict(age=30, gender=0, severity=1, duration_days=3,
    clinical_symptoms='I have fatigue and feel very tired all the time',
    fever=False)
names2 = [c['raw_name'].lower() if c.get('raw_name') else c['name'].lower() for c in r2['likely_conditions']]
blocked = [n for n in names2 if any(b in n for b in ['cancer','aids','hiv','diabetes','tuberculosis'])]
print('Conditions:', [c['name'] for c in r2['likely_conditions']])
print('Blocked high-severity:', blocked)
assert len(blocked) == 0, f'FAIL - blacklist did not block: {blocked}'
print('PASS - blacklist correctly suppressed high-severity diseases')
print()

print('=== TEST 3: Emergency — chest pain + breathlessness ===')
r3 = orc.predict(age=55, gender=1, severity=3, duration_days=1,
    clinical_symptoms='severe chest pain and i cannot breathe properly',
    chest_pain=True, breathlessness=True, fever=False)
print('Conditions:', [c['name'] for c in r3['likely_conditions']])
print('Emergency:', r3['emergency'])
print('Risk level:', r3['risk_level'])
assert r3['emergency'] == True or r3['risk_level'] in ['Emergency','High'], 'FAIL - emergency not flagged'
print('PASS - emergency correctly flagged')
print()

print('=== TEST 4: Low confidence fallback (vague input) ===')
r4 = orc.predict(age=30, gender=0, severity=1, duration_days=1,
    clinical_symptoms='i feel a bit off today')
print('Conditions count:', len(r4['likely_conditions']))
print('Confidence:', r4['confidence'])
print('Disease:', r4['disease'])
print()

print('=== TEST 5: Rural boost — viral fever surfaces ===')
r5 = orc.predict(age=22, gender=1, severity=1, duration_days=3,
    clinical_symptoms='I have fever headache and body ache for 3 days',
    fever=True, headache=True)
print('Conditions:', [c['name'] for c in r5['likely_conditions']])
print('Rules:', r5['rules_applied'])
print()

print('ALL TESTS COMPLETE')
