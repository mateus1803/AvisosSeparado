var users = [
    { username: "admin", password: "Process2030*" },
    { username: "guilherme", password: "guilherme2030" },
    { username: "ivan", password: "ivan2030" },
    { username: "carlos", password: "carlos2030" },
    { username: "ivan", password: "ivan2030" },
    { username: "ivan", password: "ivan2030" }
    // Adicione quantos usuários quiser
];

function validateLogin() {
    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;

    // Verificar se as credenciais são válidas
    for (var i = 0; i < users.length; i++) {
        if (username === users[i].username && password === users[i].password) {
            // Redirecionar para a página apropriada com base no tipo de usuário
            if (username === "admin" || username === "guilherme" || username === "ivan" || username === "carlos") {
                window.location.href = "/admin";
            } else {
                window.location.href = "/messages";
            }
            return false; // Impede o envio do formulário
        }
    }
    
    // Exibir mensagem de erro se as credenciais não forem encontradas
    alert("Usuário ou senha inválidos");
    return false;
}
