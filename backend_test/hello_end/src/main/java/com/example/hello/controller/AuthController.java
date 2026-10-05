package com.example.hello.controller;

import com.example.hello.dto.LoginRequest;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.context.SecurityContextRepository;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * 登录接口：POST /login，请求体为 JSON {"username":"...","password":"..."}
 */
@RestController
public class AuthController {

    private final AuthenticationManager authenticationManager;
    private final SecurityContextRepository securityContextRepository;

    public AuthController(AuthenticationManager authenticationManager,
                          SecurityContextRepository securityContextRepository) {
        this.authenticationManager = authenticationManager;
        this.securityContextRepository = securityContextRepository;
    }

    /**
     * 用户名密码登录
     * 认证成功：200 + 成功响应，并将认证信息写入 Session
     * 认证失败：由下方异常处理器统一返回 401
     */
    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> login(@RequestBody LoginRequest loginRequest,
                                                     HttpServletRequest request,
                                                     HttpServletResponse response) {
        // 1. 构造未认证的用户名密码令牌
        UsernamePasswordAuthenticationToken authenticationToken =
                UsernamePasswordAuthenticationToken.unauthenticated(
                        loginRequest.getUsername(), loginRequest.getPassword());

        // 2. 执行认证（账号/密码错误时抛出 AuthenticationException）
        Authentication authentication = authenticationManager.authenticate(authenticationToken);

        // 3. 认证通过：构建 SecurityContext 并持久化到 HttpSession，后续请求凭会话即已登录
        SecurityContext securityContext = SecurityContextHolder.createEmptyContext();
        securityContext.setAuthentication(authentication);
        SecurityContextHolder.setContext(securityContext);
        securityContextRepository.saveContext(securityContext, request, response);

        // 4. 返回成功响应
        Map<String, Object> result = Map.of(
                "code", 200,
                "message", "登录成功",
                "data", Map.of("username", authentication.getName()));
        return ResponseEntity.ok(result);
    }

    /**
     * 统一处理认证失败（如用户名或密码错误），返回 401
     */
    @ExceptionHandler(AuthenticationException.class)
    public ResponseEntity<Map<String, Object>> handleAuthenticationException(AuthenticationException e) {
        Map<String, Object> result = Map.of(
                "code", 401,
                "message", "用户名或密码错误");
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(result);
    }
}
