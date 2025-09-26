FROM golang:1.21-alpine as builder

WORKDIR /app

# Копируем go.mod и go.sum
COPY go.mod go.sum ./

# Скачиваем зависимости
RUN go mod download

# Копируем исходный код
COPY . .

# Собираем приложение
RUN go build -o main {{BUILD_FLAGS}}

# Финальный образ
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

# Копируем бинарник из стадии сборки
COPY --from=builder /app/main .

# Определяем точку входа
CMD ["./main"]

# Экспонируем порт (если нужно)
EXPOSE 8080