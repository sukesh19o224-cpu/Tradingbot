#!/usr/bin/env python3
"""Check if all imports are available"""

import sys

# Third-party packages that should be installed
third_party_imports = [
    'numpy',
    'pandas', 
    'scipy',
    'yfinance',
    'sklearn',  # scikit-learn
    'requests',
    'discord_webhook',
    'streamlit',
    'plotly',
    'dotenv',  # python-dotenv
    'pytz',
    'colorama',
    'sqlalchemy',
    'tabulate'  # This might be missing
]

missing = []
for package in third_party_imports:
    try:
        __import__(package)
        print(f"✅ {package}")
    except ImportError:
        print(f"❌ {package} - NOT INSTALLED")
        missing.append(package)

print("\n" + "="*60)
if missing:
    print(f"⚠️  Missing {len(missing)} package(s):")
    for pkg in missing:
        print(f"   - {pkg}")
    sys.exit(1)
else:
    print("✅ All required packages are installed!")
    sys.exit(0)
