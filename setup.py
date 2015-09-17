from distutils.core import setup

setup(
    name='journal_bot',
    version='1.0.0',
    packages=['journal_bot',
              'journal_bot.components',
              'journal_bot.components.commands',
              ],
    url='',
    license='BSD',
    author='Robert Robinson',
    author_email='rerobins@meerkatlabs.org',
    description='Journal bot for the Rho infrastructure',
    install_requires=['rhobot==1.0.0', ]
)
