package com.example.hello.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * HelloWorld 接口（受 Spring Security 保护，必须登录后才能访问）
 */
@RestController
public class HelloController {

    /**
     * GET /hello
     * 返回纯文本 "Hello World"（String 返回值由 StringHttpMessageConverter 以 text/plain 输出）
     */
    @GetMapping("/hello")
    public String hello() {
        return "Hello World";
    }
}
