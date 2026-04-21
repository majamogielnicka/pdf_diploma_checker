'''
Męczy Cię ciągłe debugowanie outputów z ekstrakcji czytając surowe dane z jsona? Masz szczęście! Bo mnie też!
Tu jest narzędzie które wizualizuje wszystkie struktury otaczając je kolorowymi bounding boxami.
'''
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple

try:
	import fitz  # PyMuPDF
except Exception:  # pragma: no cover - informative runtime error
	fitz = None


def mark_bboxes_on_pdf(pdf_path: str, saving_path: str, json_path: str, structures: List[str] | None = None) -> Dict[str, List[Dict[str, Any]]]:
	"""Annotate the provided `pdf_path` with bounding boxes from `json_path`.

	- `pdf_path` must be provided; no searching is performed.
	- `structures`: optional list of structure names to restrict marking. If `None`, mark everything with a `bbox`.

	Returns a dict mapping structure-name -> list of found items with `page`, `bbox`, and `color`.
	"""
	if fitz is None:
		raise RuntimeError("PyMuPDF (fitz) is required. Install with: pip install pymupdf")

	if not pdf_path or not os.path.exists(pdf_path):
		raise FileNotFoundError(f"pdf_path does not exist: {pdf_path}")

	with open(json_path, 'r', encoding='utf-8') as fh:
		data = json.load(fh)

	doc = fitz.open(pdf_path)

	pages = data.get('pages', [])
	page_numbers = [p.get('number', idx) for idx, p in enumerate(pages)]
	offset = 0 if (page_numbers and min(page_numbers) == 0) else 1

	# basic color palette
	colors = {
		'span': (1, 0, 0),
		'line': (0, 1, 0),
		'block': (0, 0, 1),
		'image': (1, 0.5, 0),
		'table': (0.6, 0, 0.6),
		'header': (0, 1, 1),
		'toc': (1, 1, 0),
	}

	def norm_name(s: str) -> str:
		if not isinstance(s, str):
			return ''
		s = s.lower()
		if s.endswith('ies'):
			return s[:-3] + 'y'
		if s.endswith('s'):
			return s[:-1]
		return s

	filter_set = None
	if structures is not None:
		filter_set = {norm_name(x) for x in structures}

	def to_rect(bbox: List[float]):
		return fitz.Rect(*bbox)

	def draw_rect_on_page(page, bbox: List[float], color: Tuple[float, float, float], width: float = 1.0) -> None:
		try:
			r = to_rect(bbox)
			page.draw_rect(r, color=color, width=width)
		except Exception:
			return

	def structure_matches(path_keys: List[Any]) -> bool:
		if filter_set is None:
			return True
		# check any string key in path for match
		for k in reversed(path_keys):
			if isinstance(k, str):
				if norm_name(k) in filter_set:
					return True
				# also check full key
				if k.lower() in filter_set:
					return True
		return False

	def pick_color(path_keys: List[Any]) -> Tuple[float, float, float]:
		# pick based on last string key
		for k in reversed(path_keys):
			if isinstance(k, str):
				n = norm_name(k)
				if n in colors:
					return colors[n]
		# fallback
		return (0.2, 0.2, 0.2)

	# accumulation of found structures
	found: Dict[str, List[Dict[str, Any]]] = {}

	def record_found(name: str, page_num: int, bbox: List[float], color: Tuple[float, float, float]) -> None:
		lst = found.setdefault(name, [])
		lst.append({
			'page': int(page_num),
			'bbox': [float(x) for x in bbox],
			'color': [float(x) for x in color],
		})

	# recursive walker
	def walk(obj: Any, path: List[Any], current_page: Any = None) -> None:
		if isinstance(obj, dict):
			# if this dict itself has bbox, consider drawing it
			if 'bbox' in obj and structure_matches(path):
				bbox = obj.get('bbox')
				if bbox and isinstance(bbox, (list, tuple)) and len(bbox) == 4:
					# determine page
					page_num = obj.get('page') or obj.get('page_num') or obj.get('pageNumber') or current_page
					if page_num is None:
						# try searching for numeric 'number' key
						page_num = obj.get('number')
					if page_num is None:
						return
					try:
						idx = int(page_num) - offset
						if 0 <= idx < len(doc):
							col = pick_color(path)
							draw_rect_on_page(doc[idx], [float(x) for x in bbox], col)
							# determine a canonical name for this structure
							sname = 'unknown'
							for k in reversed(path):
								if isinstance(k, str):
									sname = norm_name(k)
									break
							record_found(sname, page_num, bbox, col)
					except Exception:
						return
			# continue walking
			for k, v in obj.items():
				walk(v, path + [k], current_page)
		elif isinstance(obj, list):
			for i, item in enumerate(obj):
				walk(item, path + [i], current_page)
		else:
			return

	# Walk pages first, passing page context so nested bboxes get the page number
	for i, p in enumerate(pages):
		page_num = p.get('number', i)
		walk(p, ['pages', i], current_page=page_num)

	# Walk other top-level keys
	for k, v in data.items():
		if k == 'pages':
			continue
			# for top-level items we don't have page context
		walk(v, [k], current_page=None)

	# Save annotated PDF
	doc.save(saving_path, garbage=4, deflate=True)
	doc.close()


__all__ = ["mark_bboxes_on_pdf"]


