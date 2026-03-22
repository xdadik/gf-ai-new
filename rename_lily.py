import os

def replace_in_file(filepath, replacements):
    if not os.path.exists(filepath): return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

replace_in_file('templates/dashboard.html', [
    ('Nova Bot Dashboard', 'Lily AI Dashboard'),
    ('Nova Bot', 'Lily'),
    ('nova bot', 'lily')
])

replace_in_file('run_with_dashboard.py', [
    ('Nova', 'Lily'),
    ('nova', 'lily'),
    ('NOVA', 'LILY')
])

replace_in_file('dashboard.py', [
    ('nova', 'lily'),
    ('Nova', 'Lily'),
    ('NOVA', 'LILY')
])

replace_in_file('personalities.py', [
    ('NOVA_BACKSTORY', 'LILY_BACKSTORY'),
    ('NOVA_MEMORY_GUIDELINES', 'LILY_MEMORY_GUIDELINES'),
    ('Nova Personality System', 'Lily Personality System'),
    ('Nova\'s Backstory', 'Lily\'s Backstory'),
    ('I am Nova', 'I am Lily'),
    ('Nova remembers', 'Lily remembers'),
    ('novabot', 'lilybot'),
    ('"nova"', '"lily"'),
    ('get_personality("nova")', 'get_personality("lily")')
])

replace_in_file('skills_module.py', [
    ('Skills Module for Nova', 'Skills Module for Lily'),
    ('Nova', 'Lily'),
    ('nova', 'lily')
])

replace_in_file('README.md', [
    ('Nova', 'Lily'),
    ('nova', 'lily'),
    ('NOVA', 'LILY')
])

replace_in_file('PRIVACY_NOTICE.txt', [
    ('Nova', 'Lily')
])

replace_in_file('nova_bot.py', [
    ('NovaBot', 'LilyBot'),
    ('Nova wants to run', 'Lily wants to run'),
    ('Nova:', 'Lily:'),
    ('Nova is retrieving', 'Lily is retrieving'),
    ('Nova only responds', 'Lily only responds'),
    ('Nova:', 'Lily:'),
    ('key or "nova"', 'key or "lily"'),
    ('[System: The user just started the bot. Greet them warmly as Lily.', '[System: The user just started the bot. Greet them warmly as Lily.')
])

