# project_mapper.py
PROJECT_EXCLUDES = {
    "Python": ["__pycache__", "venv", "env", "build", "dist"],
    "Java": ["target", "out", ".idea", ".settings"],
    "Angular": ["node_modules", "dist"],
    "React": ["node_modules", "build"],
    "Vue.js": ["node_modules", "dist"],
    "Laravel": ["vendor", "node_modules", "storage/logs"],
    "PHP": ["vendor"],
    "Node.js": ["node_modules"],
}
