#!/usr/bin/env python3
"""Bisect Direct File fact-graph module loading failures using the subset harness."""

from __future__ import annotations

import xml.etree.ElementTree as ET
import subprocess
import os
from pathlib import Path


ROOT = Path("/Users/tkhan/IdeaProjects/taxes/direct-file-easy-webui/direct-file/backend")
TIMEOUT_SECONDS = 30
TEST_NAME = "gov.irs.directfile.api.ats.FactDictionarySubsetLoadTest#loadsSelectedFactDictionaryModules"
JAVA_HOME = "/opt/homebrew/Cellar/openjdk@21/21.0.10/libexec/openjdk.jdk/Contents/Home"
TAX_XML_DIR = ROOT / "src/main/resources/tax"


def build_module_metadata() -> tuple[dict[str, set[str]], dict[str, list[str]], dict[str, set[str]]]:
    module_paths: dict[str, set[str]] = {}
    path_to_modules: dict[str, list[str]] = {}
    explicit_module_deps: dict[str, set[str]] = {}

    for xml_path in sorted(TAX_XML_DIR.glob("*.xml")):
        module = xml_path.stem
        root = ET.parse(xml_path).getroot()
        module_paths[module] = set()
        explicit_module_deps[module] = set()
        for fact in root.findall(".//Fact"):
            fact_path = fact.attrib.get("path")
            if fact_path:
                module_paths[module].add(fact_path)
                path_to_modules.setdefault(fact_path, []).append(module)
            for dep in fact.findall(".//Dependency"):
                dep_module = dep.attrib.get("module")
                if dep_module:
                    explicit_module_deps[module].add(dep_module)

    return module_paths, path_to_modules, explicit_module_deps


MODULE_PATHS, PATH_TO_MODULES, EXPLICIT_MODULE_DEPS = build_module_metadata()


def expand_subset(modules: list[str]) -> list[str]:
    expanded = set(modules)
    changed = True
    while changed:
        changed = False
        current = sorted(expanded)
        for module in current:
            for dep_module in EXPLICIT_MODULE_DEPS.get(module, set()):
                if dep_module not in expanded:
                    expanded.add(dep_module)
                    changed = True

        provided_paths = set()
        for module in expanded:
            provided_paths.update(MODULE_PATHS.get(module, set()))

        for module in current:
            xml_path = TAX_XML_DIR / f"{module}.xml"
            root = ET.parse(xml_path).getroot()
            for dep in root.findall(".//Dependency"):
                dep_path = dep.attrib.get("path")
                if not dep_path or dep_path in provided_paths:
                    continue
                providers = PATH_TO_MODULES.get(dep_path, [])
                if len(providers) == 1 and providers[0] not in expanded:
                    expanded.add(providers[0])
                    changed = True
    return sorted(expanded)


def run_subset(modules: list[str]) -> bool:
    modules = expand_subset(modules)
    command = [
        "./mvnw",
        "-q",
        f"-Dtest={TEST_NAME}",
        f"-Dsubset.modules={','.join(modules)}",
        "-DforkCount=0",
        "-Dsurefire.useFile=false",
        "-Dpmd.skip=true",
        "-Dspotbugs.skip=true",
        "-Dcheckstyle.skip=true",
        "test",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env={**os.environ, "JAVA_HOME": JAVA_HOME},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT ({len(modules)} modules): {','.join(modules)}", flush=True)
        return False

    ok = completed.returncode == 0
    status = "PASS" if ok else f"FAIL:{completed.returncode}"
    print(f"{status} ({len(modules)} modules): {','.join(modules)}", flush=True)
    if not ok:
        print(completed.stdout[-4000:], flush=True)
    return ok


def bisect(modules: list[str]) -> list[str]:
    if len(modules) <= 1:
        return modules

    midpoint = len(modules) // 2
    left = modules[:midpoint]
    right = modules[midpoint:]

    left_ok = run_subset(left)
    right_ok = run_subset(right)

    if not left_ok and left:
        return bisect(left)
    if not right_ok and right:
        return bisect(right)
    return modules


def main() -> int:
    modules = sorted(path.stem for path in TAX_XML_DIR.glob("*.xml"))
    failing = bisect(modules)
    print("Possible failing subset:", ",".join(failing), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
