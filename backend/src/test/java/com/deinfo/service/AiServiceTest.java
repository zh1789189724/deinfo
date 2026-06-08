package com.deinfo.service;

import com.deinfo.config.DeepSeekConfig;
import com.deinfo.dto.AIClassifyRequest;
import com.deinfo.dto.AIClassifyResponse;
import com.deinfo.dto.AITranslateRequest;
import com.deinfo.dto.AITranslateResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AiServiceTest {

    @Mock
    private DeepSeekConfig deepSeekConfig;
    @Mock
    private WebClient webClient;
    @Mock
    private WebClient.RequestBodyUriSpec requestBodyUriSpec;
    @Mock
    private WebClient.RequestHeadersSpec requestHeadersSpec;
    @Mock
    private WebClient.ResponseSpec responseSpec;

    private ObjectMapper objectMapper;
    private AiService aiService;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        when(deepSeekConfig.getApiKey()).thenReturn("test-api-key");
        when(deepSeekConfig.getApiUrl()).thenReturn("https://api.deepseek.com/v1/chat/completions");
        aiService = new AiService(deepSeekConfig, webClient, objectMapper);
    }

    private void mockDeepSeekCall(String responseBody) {
        when(webClient.post()).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.uri(anyString())).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.header(anyString(), anyString())).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.bodyValue(any())).thenReturn(requestHeadersSpec);
        when(requestHeadersSpec.retrieve()).thenReturn(responseSpec);
        when(responseSpec.bodyToMono(String.class)).thenReturn(Mono.just(responseBody));
    }

    // ── classify ─────────────────────────────────────

    @Test
    @DisplayName("classify 正常返回应解析 JSON 内容")
    void classify_validResponse() {
        String deepSeekResponse = """
            {
                "choices": [{
                    "message": {
                        "content": "{\\"category\\": \\"消费券\\", \\"tags\\": [\\"成都\\", \\"补贴\\"], \\"summary\\": \\"成都发放新一轮消费券\\", \\"score\\": 85}"
                    }
                }]
            }
            """;
        mockDeepSeekCall(deepSeekResponse);

        AIClassifyRequest req = new AIClassifyRequest();
        req.setContent("成都发放消费券");
        req.setContext("deal");
        AIClassifyResponse result = aiService.classify(req);

        assertThat(result).isNotNull();
        assertThat(result.getCategory()).isEqualTo("消费券");
        assertThat(result.getTags()).contains("成都", "补贴");
        assertThat(result.getSummary()).isEqualTo("成都发放新一轮消费券");
        assertThat(result.getScore()).isEqualTo(85);
    }

    @Test
    @DisplayName("classify API 返回空 choices 时返回降级默认值")
    void classify_emptyChoices_returnsDefault() {
        String deepSeekResponse = """
            {"choices": []}
            """;
        mockDeepSeekCall(deepSeekResponse);

        AIClassifyRequest req = new AIClassifyRequest();
        req.setContent("测试内容");
        AIClassifyResponse result = aiService.classify(req);

        assertThat(result).isNotNull();
        assertThat(result.getCategory()).isEqualTo("other");
        assertThat(result.getScore()).isEqualTo(50);
    }

    @Test
    @DisplayName("classify API 调用失败时重试后返回降级默认值")
    void classify_apiError_retryAndFallback() {
        when(webClient.post()).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.uri(anyString())).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.header(anyString(), anyString())).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.bodyValue(any())).thenReturn(requestHeadersSpec);
        when(requestHeadersSpec.retrieve()).thenReturn(responseSpec);
        when(responseSpec.bodyToMono(String.class))
            .thenThrow(new RuntimeException("Connection refused"));

        AIClassifyRequest req = new AIClassifyRequest();
        req.setContent("测试内容");
        AIClassifyResponse result = aiService.classify(req);

        // 应返回降级默认值，而非抛出异常
        assertThat(result).isNotNull();
        assertThat(result.getCategory()).isEqualTo("other");
        assertThat(result.getScore()).isEqualTo(50);
        // 验证重试了多次
        verify(responseSpec, atLeast(2)).bodyToMono(String.class);
    }

    @Test
    @DisplayName("classify 相同内容走缓存，不重复调用 API")
    void classify_cacheHit_skipsApiCall() {
        String deepSeekResponse = """
            {
                "choices": [{
                    "message": {
                        "content": "{\\"category\\": \\"消费券\\", \\"tags\\": [], \\"summary\\": \\"消费券\\", \\"score\\": 80}"
                    }
                }]
            }
            """;
        mockDeepSeekCall(deepSeekResponse);

        AIClassifyRequest req = new AIClassifyRequest();
        req.setContent("成都消费券");
        req.setContext("deal");

        // 第一次调用
        aiService.classify(req);
        // 第二次调用（相同内容）
        AIClassifyResponse result = aiService.classify(req);

        assertThat(result.getCategory()).isEqualTo("消费券");
        // WebClient.post() 应该只被调用一次（第二次走缓存）
        verify(webClient, times(1)).post();
    }

    @Test
    @DisplayName("classify 不同内容不共享缓存")
    void classify_differentContent_differentCache() {
        String response1 = """
            {
                "choices": [{
                    "message": {
                        "content": "{\\"category\\": \\"消费券\\", \\"tags\\": [], \\"summary\\": \\"a\\", \\"score\\": 80}"
                    }
                }]
            }
            """;
        String response2 = """
            {
                "choices": [{
                    "message": {
                        "content": "{\\"category\\": \\"美食\\", \\"tags\\": [], \\"summary\\": \\"b\\", \\"score\\": 70}"
                    }
                }]
            }
            """;

        when(webClient.post()).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.uri(anyString())).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.header(anyString(), anyString())).thenReturn(requestBodyUriSpec);

        // 第一次返回 response1
        when(requestBodyUriSpec.bodyValue(any())).thenReturn(requestHeadersSpec);
        when(requestHeadersSpec.retrieve()).thenReturn(responseSpec);
        when(responseSpec.bodyToMono(String.class)).thenReturn(Mono.just(response1));

        AIClassifyRequest req1 = new AIClassifyRequest();
        req1.setContent("成都消费券");
        aiService.classify(req1);

        // 第二次返回 response2（不同内容）
        when(responseSpec.bodyToMono(String.class)).thenReturn(Mono.just(response2));
        AIClassifyRequest req2 = new AIClassifyRequest();
        req2.setContent("成都美食推荐");
        AIClassifyResponse result2 = aiService.classify(req2);

        assertThat(result2.getCategory()).isEqualTo("美食");
        // 两次不同内容，API 应被调用两次
        verify(responseSpec, times(2)).bodyToMono(String.class);
    }

    // ── translate ────────────────────────────────────

    @Test
    @DisplayName("translate 正常返回应解析 JSON 内容")
    void translate_validResponse() {
        String deepSeekResponse = """
            {
                "choices": [{
                    "message": {
                        "content": "{\\"titleCn\\": \\"新产品\\", \\"contentCn\\": \\"这是一个新产品描述\\", \\"summaryCn\\": \\"新产品的简要摘要\\"}"
                    }
                }]
            }
            """;
        mockDeepSeekCall(deepSeekResponse);

        AITranslateRequest req = new AITranslateRequest();
        req.setContent("New product description");
        req.setTargetLang("zh");
        AITranslateResponse result = aiService.translate(req);

        assertThat(result).isNotNull();
        assertThat(result.getTitleCn()).isEqualTo("新产品");
        assertThat(result.getContentCn()).isEqualTo("这是一个新产品描述");
        assertThat(result.getSummaryCn()).isEqualTo("新产品的简要摘要");
    }

    @Test
    @DisplayName("translate API 失败时返回降级默认值")
    void translate_apiError_returnsDefault() {
        when(webClient.post()).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.uri(anyString())).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.header(anyString(), anyString())).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.bodyValue(any())).thenReturn(requestHeadersSpec);
        when(requestHeadersSpec.retrieve()).thenReturn(responseSpec);
        when(responseSpec.bodyToMono(String.class))
            .thenThrow(new RuntimeException("API error"));

        AITranslateRequest req = new AITranslateRequest();
        req.setContent("Test content");
        AITranslateResponse result = aiService.translate(req);

        assertThat(result).isNotNull();
        // 降级返回原文
        assertThat(result.getTitleCn()).contains("Test");
    }

    @Test
    @DisplayName("translate 相同内容走缓存")
    void translate_cacheHit_skipsApiCall() {
        String deepSeekResponse = """
            {
                "choices": [{
                    "message": {
                        "content": "{\\"titleCn\\": \\"测试\\", \\"contentCn\\": \\"测试内容\\", \\"summaryCn\\": \\"摘要\\"}"
                    }
                }]
            }
            """;
        mockDeepSeekCall(deepSeekResponse);

        AITranslateRequest req = new AITranslateRequest();
        req.setContent("Test");
        req.setTargetLang("zh");

        aiService.translate(req);
        AITranslateResponse result = aiService.translate(req);

        assertThat(result.getTitleCn()).isEqualTo("测试");
        verify(webClient, times(1)).post();
    }

    @Test
    @DisplayName("classify 返回 JSON 缺失字段时使用降级默认值")
    void classify_missingFields_usesDefaults() {
        String deepSeekResponse = """
            {
                "choices": [{
                    "message": {
                        "content": "{\\"category\\": \\"科技\\"}"
                    }
                }]
            }
            """;
        mockDeepSeekCall(deepSeekResponse);

        AIClassifyRequest req = new AIClassifyRequest();
        req.setContent("AI 技术突破");
        AIClassifyResponse result = aiService.classify(req);

        assertThat(result.getCategory()).isEqualTo("科技");
        assertThat(result.getTags()).isNotNull();  // 缺失 tags 应返回空列表
        assertThat(result.getScore()).isEqualTo(50); // 缺失 score 应使用默认值
    }
}
