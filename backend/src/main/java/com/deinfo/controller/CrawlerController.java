package com.deinfo.controller;

import com.deinfo.entity.Deal;
import com.deinfo.entity.GlobalContent;
import com.deinfo.service.ContentService;
import com.deinfo.service.GlobalService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/crawler")
@RequiredArgsConstructor
public class CrawlerController {

    private final ContentService contentService;
    private final GlobalService globalService;

    /**
     * Crawler pushes content data to backend.
     * Dispatches based on source type:
     *   domestic -> ContentService (classify)
     *   overseas -> GlobalService (classify + translate)
     */
    @PostMapping("/push")
    public ResponseEntity<?> push(@RequestBody Map<String, Object> payload) {
        String sourceType = (String) payload.get("sourceType");
        Map<String, Object> contentData = (Map<String, Object>) payload.get("content");
        String lang = (String) payload.get("lang");

        if (contentData == null) {
            return ResponseEntity.badRequest().body(Map.of("error", "content is required"));
        }

        try {
            if ("domestic".equals(sourceType)) {
                // Domestic sources: classify only
                Deal deal = contentService.processAndSave(contentData);
                return ResponseEntity.ok(Map.of(
                    "type", "domestic",
                    "deal", deal
                ));
            } else {
                // Overseas sources: classify + translate
                GlobalContent gc = globalService.processAndSave(contentData);
                return ResponseEntity.ok(Map.of(
                    "type", "overseas",
                    "content", gc
                ));
            }
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of(
                "error", "Processing failed: " + e.getMessage()
            ));
        }
    }

    /**
     * Bulk push from crawler (multiple items at once)
     */
    @PostMapping("/push-bulk")
    public ResponseEntity<?> pushBulk(@RequestBody Map<String, Object> payload) {
        List<Map<String, Object>> items = (List<Map<String, Object>>) payload.get("items");
        String sourceType = (String) payload.get("sourceType");
        String lang = (String) payload.get("lang");

        int success = 0;
        int failed = 0;

        for (Map<String, Object> item : items) {
            try {
                if ("domestic".equals(sourceType)) {
                    contentService.processAndSave(item);
                } else {
                    globalService.processAndSave(item);
                }
                success++;
            } catch (Exception e) {
                failed++;
            }
        }

        return ResponseEntity.ok(Map.of(
            "total", items.size(),
            "success", success,
            "failed", failed
        ));
    }
}
