# Blender-side scripts

`operations.py` and `__init__.py` are licensed **GPL-3.0-or-later**, under
[the GNU General Public License version 3](LICENSE), or any later version.
They execute inside Blender and use Blender/Bonsai APIs. The external host,
runner and tests are covered by the repository's root MIT licence.

The runner invokes `operations.py` in a separate Blender process with JSON
requests and IFC files. Blender and Bonsai are runtime dependencies, not vendored
code. The review result does not require either application.
