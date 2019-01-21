from setuptools import setup, find_packages

setup(
    name='gumtree_watchdog',
    author='Shane Matuszek',
    packages=find_packages(),
    install_requires=['python-telegram-bot', 'scrapy'],
    entry_points={
        'console_scripts': [
            'gumtree_watchdog_api=gumtree_watchdog.telegram_app:main',
            'gumtree_watchdog_cron=gumtree_watchdog.cron_app:main'
        ]
    })
