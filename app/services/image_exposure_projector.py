# app/services/image_exposure_projector.py

from typing import Dict, List, Any


class ImageExposureProjector:

    def project(
        self,
        *,
        stage: str,
        image_refs: Dict[str, Any] | None,
    ) -> List[Dict[str, str]]:

        if not image_refs:
            return []

        before = image_refs.get("antes") or []
        during = image_refs.get("durante") or []
        after = image_refs.get("depois") or []

        def ensure_list(value):
            if isinstance(value, list):
                return value
            return [value]

        before_list = ensure_list(before)
        during_list = ensure_list(during)
        after_list = ensure_list(after)

        result = []

        if stage == "summary":
            return []

        if stage == "partial":
            if before_list:
                return [{"type": "before", "path": before_list[0]}]
            if during_list:
                return [{"type": "during", "path": during_list[0]}]
            if after_list:
                return [{"type": "after", "path": after_list[0]}]
            return []

        # FULL
        for path in before_list:
            result.append({"type": "before", "path": path})

        for path in during_list:
            result.append({"type": "during", "path": path})

        for path in after_list:
            result.append({"type": "after", "path": path})

        return result
