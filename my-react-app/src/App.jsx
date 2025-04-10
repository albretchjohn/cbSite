import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import React, { useEffect, useRef} from 'react';

function App() {
  // const [count, setCount] = useState(0)

  const [countdown, setCountdown] = useState(10);
  const [gameStarted, setGameStarted] = useState(false);
  const [currentImage, setCurrentImage] = useState(0);
  const [imageUrl, setImageUrl] = useState('');
  const [guess, setGuess] = useState('');
  const [result, setResult] = useState('');
  const [score, setScore] = useState(0);
  const [correctAnswers, setCorrectAnswers] = useState([]);
  const [correctGuesses, setCorrectGuesses] = useState(0);
  const [incorrectGuesses, setIncorrectGuesses] = useState(0);

  const timerRef = useRef(null);

  const generatePlate = async () => {
    const number = Math.floor(Math.random() * 99) + 1;
    const response = await fetch('http://127.0.0.1:5000/generate_plate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ number }),
    });

    if (response.ok) {
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setImageUrl(url);
      setCorrectAnswers(prev => [...prev, number]);
    } else {
      alert('Failed to generate plate');
    }
  };

  const startGame = async () => {
    setGameStarted(true);
    setCurrentImage(0);
    setCorrectGuesses(0);
    setIncorrectGuesses(0);
    await nextImage();
  };

  const nextImage = async () => {
    await generatePlate();
    setCountdown(10);
    setResult('');
    clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timerRef.current);
          checkGuess(); // auto check
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const checkGuess = () => {
    clearInterval(timerRef.current);
    const correct = correctAnswers[correctAnswers.length - 1];
    const userGuess = parseInt(guess);
    if (userGuess === correct) {
      setResult('Correct!');
      setCorrectGuesses(prev => prev + 1);
    } else {
      setResult('Wrong!');
      setIncorrectGuesses(prev => prev + 1);
    }
    setTimeout(() => {
      if (currentImage + 1 < 11) {
        setCurrentImage(prev => prev + 1);
        nextImage();
      } else {
        endGame();
      }
    }, 2000);
  };

  const endGame = () => {
    clearInterval(timerRef.current);
    window.location.href = `score.html?score=${correctGuesses}`;
  };

  return (
    <>
      <div className="container">
        <div className="game-column">
          <h1>Eyes Test Game</h1>
          <div id="imageContainer">
            <img id="gameImage" src="" alt="Guess the number" />
          </div>
        </div>
        <div className="info-column">
          <div className="info-row">
            <div className="countdown">
              <div id="countdown">10</div>
            </div>
            <button id="startBtn">Start</button>
          </div>
          <input type="number" id="guessInput" placeholder="what you see enter here" />
          <br />
          <br />
          <button id="submitBtn">Submit</button>
          {/* <button id="nextBtn" style={{ display: "none" }}>Next Image</button> */}
          <div id="result"></div>
          <div id="score">Score: 0</div>
        </div>
      </div>
      
    </>
  )
}

export default App
