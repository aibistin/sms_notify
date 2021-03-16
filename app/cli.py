import os
import click


def register(app):
    @app.cli.group()
    def test_comd():
        """Just a test command"""
        pass
