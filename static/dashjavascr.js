const input = document.getElementById('input');
const output = document.getElementById('output');

function printInput(){
  output.innerHTML = input.value;
}

input.addEventListener("keyup", function() {
    document.getElementById("button").click();
  });