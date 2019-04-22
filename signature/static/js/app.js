var wrapper = document.getElementById("signature-pad");
var clearButton = wrapper.querySelector("[data-action=clear]");
var changeColorButton = wrapper.querySelector("[data-action=change-color]");
var undoButton = wrapper.querySelector("[data-action=undo]");
var savePNGButton = wrapper.querySelector("[data-action=save-png]");
var saveJPGButton = wrapper.querySelector("[data-action=save-jpg]");
var saveSVGButton = wrapper.querySelector("[data-action=save-svg]");
var canvas = wrapper.querySelector("canvas");
var signaturePad = new SignaturePad(canvas, {
    // It's Necessary to use an opaque color when saving image as JPEG;
    // this option can be omitted if only saving as PNG or SVG
    backgroundColor: 'rgb(255, 255, 255)'
});
var service_id = document.getElementById("service_id");
// Adjust canvas coordinate space taking into account pixel ratio,
// to make it look crisp on mobile devices.
// This also causes canvas to be cleared.
function resizeCanvas() {
    // When zoomed out to less than 100%, for some very strange reason,
    // some browsers report devicePixelRatio as less than 1
    // and only part of the canvas is cleared then.
    var ratio = Math.max(window.devicePixelRatio || 1, 1);

    // This part causes the canvas to be cleared
    canvas.width = canvas.offsetWidth * ratio;
    canvas.height = canvas.offsetHeight * ratio;
    canvas.getContext("2d").scale(ratio, ratio);

    // This library does not listen for canvas changes, so after the canvas is automatically
    // cleared by the browser, SignaturePad#isEmpty might still return false, even though the
    // canvas looks empty, because the internal data of this library wasn't cleared. To make sure
    // that the state of this library is consistent with visual state of the canvas, you
    // have to clear it manually.
    signaturePad.clear();
}

// On mobile devices it might make more sense to listen to orientation change,
// rather than window resize events.
window.onresize = resizeCanvas;
resizeCanvas();

function download(dataURL, filename) {
    //print (dataURL)
    var blob = dataURLToBlob(dataURL);
    var url = window.URL.createObjectURL(blob);  //blob로 서명 데이터 참조를 가리키는 url 객체 : 파일의 전체 내용을 URL 텍스트로 변환한 값

    var fileType = "blob";
    var fileName = filename + ".jpg";
    var a = document.createElement("a");
    a.style = "display: none";
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);

    var form_data = new FormData();
    form_data.append('file', blob);

    signatureUrl = '/signature/saveimg/'+ filename + "/";
    // console.log(signatureUrl);
    $.ajax({
        url: signatureUrl,
        method: 'POST',
        cache: false,
        contentType: false,
        processData: false,
        data: form_data,
        headers: {'X-CSRFToken': '{{ csrf_token }}'},
        success: function () {
            load_url = "/mail/" + filename + "/";
            window.URL.revokeObjectURL(url);
            location.href = load_url
        }
    });


}

// One could simply use Canvas#toBlob method instead, but it's just to show
// that it can be done using result of SignaturePad#toDataURL.
function dataURLToBlob(dataURL) {
    // Code taken from https://github.com/ebidel/filer.js
    var parts = dataURL.split(';base64,');
    var contentType = parts[0].split(":")[1];
    var raw = window.atob(parts[1]);
    var rawLength = raw.length;
    var uInt8Array = new Uint8Array(rawLength);

    for (var i = 0; i < rawLength; ++i) {
        uInt8Array[i] = raw.charCodeAt(i);
    }

    return new Blob([uInt8Array], {type: contentType});
}

clearButton.addEventListener("click", function (event) {
    signaturePad.clear();
});

undoButton.addEventListener("click", function (event) {
    var data = signaturePad.toData();

    if (data) {
        data.pop(); // remove the last dot or line
        signaturePad.fromData(data);
    }
});

changeColorButton.addEventListener("click", function (event) {
    var r = Math.round(Math.random() * 255);
    var g = Math.round(Math.random() * 255);
    var b = Math.round(Math.random() * 255);
    var color = "rgb(" + r + "," + g + "," + b + ")";

    signaturePad.penColor = color;
});

savePNGButton.addEventListener("click", function (event) {
    if (signaturePad.isEmpty()) {
        alert("Please provide a signature first.");
    } else {
        var dataURL = signaturePad.toDataURL();
        download(dataURL, "signature.png");
    }
});

saveJPGButton.addEventListener("click", function (event) {

    if (signaturePad.isEmpty()) {
        alert("서명을 해주세요.");
    } else {
        const dataURL = signaturePad.toDataURL();
        const fileName = String(service_id.value);


        const mgs = confirm("서명을 완료 하시겠습니까?");
        if (mgs) {
            download(dataURL, fileName);
        } else {
            alert("서명 확인이 취소되었습니다");
        }

    }
});

saveSVGButton.addEventListener("click", function (event) {
    if (signaturePad.isEmpty()) {
        alert("Please provide a signature first.");
    } else {
        var dataURL = signaturePad.toDataURL('image/svg+xml');
        download(dataURL, "signature.svg");
    }
});
