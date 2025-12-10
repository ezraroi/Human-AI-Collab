"""
Consolidates Anytype markdown files by object type for LLM consumption.
Creates token-efficient output files grouped by schema type.
"""

import json
import os
import re
from pathlib import Path


def load_schemas(schemas_dir: Path) -> dict[str, dict]:
    """Load all schema files and return mapping of type name to schema."""
    schemas = {}
    for schema_file in schemas_dir.glob("*.schema.json"):
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
            type_name = schema.get("title", "")
            if type_name:
                props = schema.get("properties", {})
                schemas[type_name] = {
                    "file": schema_file.name,
                    "plural": schema.get("x-plural", type_name + "s"),
                    "properties": [
                        prop for prop, details in props.items()
                        if not details.get("x-hidden", False)
                    ],
                    "has_epistemic_status": "Epistemic Status" in props
                }
    return schemas


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter and return (metadata dict, body content)."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_text = parts[1].strip()
    body = parts[2].strip()

    metadata = {}
    current_key = None
    current_list = []

    for line in frontmatter_text.split("\n"):
        # Skip comment lines
        if line.strip().startswith("#"):
            continue

        # Check for key: value pattern
        key_match = re.match(r'^([A-Za-z][A-Za-z0-9 _-]*):\s*(.*)', line)
        if key_match:
            # Save previous list if any
            if current_key and current_list:
                metadata[current_key] = current_list
                current_list = []

            key = key_match.group(1).strip()
            value = key_match.group(2).strip()
            current_key = key

            if value:
                # Single value or start of inline list
                if value.startswith('"') and value.endswith('"'):
                    metadata[key] = value.strip('"')
                elif value.startswith("'") and value.endswith("'"):
                    metadata[key] = value.strip("'")
                else:
                    metadata[key] = value
                current_key = None
            # Else wait for list items
        elif line.strip().startswith("- "):
            # List item
            item = line.strip()[2:].strip()
            if item.startswith("'") and item.endswith("'"):
                item = item[1:-1]
            elif item.startswith('"') and item.endswith('"'):
                item = item[1:-1]
            current_list.append(item)

    # Save last list if any
    if current_key and current_list:
        metadata[current_key] = current_list

    return metadata, body


def extract_title_from_body(body: str) -> str:
    """Extract title from markdown body (first # heading)."""
    for line in body.split("\n"):
        if line.strip().startswith("# "):
            return line.strip()[2:].strip()
    return ""


def get_object_type(metadata: dict) -> str:
    """Extract object type from metadata."""
    obj_type = metadata.get("Object type", "")
    if isinstance(obj_type, list):
        return obj_type[0] if obj_type else ""
    return obj_type


def format_list(items: list) -> str:
    """Format a list compactly."""
    if not items:
        return ""
    return ", ".join(str(item) for item in items)


EPISTEMIC_STATUS_SHORT = {
    "Empirical Claim: Testable biological or mechanical hypotheses": "Empirical",
    "Literature: Established academic fact": "Literature",
    "Experiential: Grounded in N=1 phenomenology/felt sense": "Experiential",
    "Theoretical Framework: Structuring ideas/axioms": "Theoretical",
}


def get_epistemic_short(status: str) -> str:
    """Convert verbose epistemic status to short form for token efficiency."""
    return EPISTEMIC_STATUS_SHORT.get(status, status)


def strip_markdown_links(text: str) -> str:
    """Remove markdown links, keeping only the display text.

    Converts [text](url) -> text and [text] -> text.
    """
    # First: [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    # Second: standalone [text] references -> text
    text = re.sub(r'\[([^\]]+)\]', r'\1', text)
    return text


def compress_whitespace(text: str) -> str:
    """Reduce multiple blank lines to single blank line for token efficiency."""
    # Replace 3+ newlines with 2 (one blank line)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove trailing whitespace from lines
    text = '\n'.join(line.rstrip() for line in text.split('\n'))
    return text.strip()


def consolidate_files(root_dir: Path, schemas: dict, output_dir: Path):
    """Group files by type and create consolidated output."""
    output_dir.mkdir(exist_ok=True)

    # Collect files by type
    files_by_type: dict[str, list[tuple[str, dict, str]]] = {t: [] for t in schemas}
    files_by_type["Unknown"] = []

    for md_file in root_dir.glob("*.md"):
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        metadata, body = parse_frontmatter(content)
        obj_type = get_object_type(metadata)

        if obj_type in files_by_type:
            files_by_type[obj_type].append((md_file.name, metadata, body))
        elif obj_type:
            files_by_type["Unknown"].append((md_file.name, metadata, body))

    # Generate output for each type
    for type_name, files in files_by_type.items():
        if not files:
            continue

        schema_info = schemas.get(type_name, {})
        plural = schema_info.get("plural", type_name + "s")

        # Create filename from plural name
        safe_filename = re.sub(r'[^\w\s-]', '', plural.lower())
        safe_filename = re.sub(r'[\s]+', '_', safe_filename)
        output_file = output_dir / f"{safe_filename}.md"

        # Pre-process to get all titles for index
        sorted_files = sorted(files, key=lambda x: x[0])
        titles = []
        for filename, metadata, body in sorted_files:
            title = extract_title_from_body(body) or filename.replace('.md', '')
            titles.append(title)

        lines = []

        # Compact header
        lines.append(f"# {plural} ({len(files)})")
        lines.append("")

        # Index for quick lookup
        lines.append("## Index")
        lines.append(", ".join(titles))
        lines.append("")
        lines.append("---")
        lines.append("")

        # Each item - compact format
        for idx, (filename, metadata, body) in enumerate(sorted_files):
            title = titles[idx]

            lines.append(f"## [{type_name.upper()}] {title}")

            # Build compact metadata line: [EpistemicStatus] Tags
            meta_parts = []

            # Add epistemic status if schema supports it and value exists
            if schema_info.get("has_epistemic_status"):
                epistemic = metadata.get("Epistemic Status", "")
                if epistemic:
                    short_status = get_epistemic_short(epistemic)
                    meta_parts.append(f"[{short_status}]")

            # Add tags
            tags = metadata.get("Tag", [])
            if tags:
                tag_str = format_list(tags) if isinstance(tags, list) else tags
                meta_parts.append(tag_str)

            if meta_parts:
                lines.append(" ".join(meta_parts))

            # Body content (strip the title since we already have it)
            body_lines = body.split("\n")
            content_start = 0
            for i, line in enumerate(body_lines):
                if line.strip().startswith("# "):
                    content_start = i + 1
                    break

            clean_body = "\n".join(body_lines[content_start:]).strip()
            if clean_body:
                clean_body = strip_markdown_links(clean_body)
                clean_body = compress_whitespace(clean_body)
                lines.append("")
                lines.append(clean_body)

            lines.append("")
            lines.append("---")
            lines.append("")

        # Write output
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"Created: {output_file.name} ({len(files)} items)")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent  # Go up one level to project root
    schemas_dir = root_dir / "schemas"
    output_dir = root_dir / "output"

    print("Loading schemas...")
    schemas = load_schemas(schemas_dir)
    print(f"Found {len(schemas)} types: {', '.join(schemas.keys())}")
    print()

    print("Processing files...")
    consolidate_files(root_dir, schemas, output_dir)
    print()
    print("Done!")


if __name__ == "__main__":
    main()

