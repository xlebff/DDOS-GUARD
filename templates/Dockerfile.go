FROM golang:1.21-alpine

WORKDIR /app

# Копируем все файлы проекта
COPY . .

# Скачиваем зависимости (если есть go.mod)
RUN if [ -f go.mod ]; then \
    go mod download; \
    fi

# Собираем приложение
RUN go build -v -o main .

EXPOSE 8080

CMD ["./main"]